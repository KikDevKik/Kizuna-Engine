use std::sync::atomic::{AtomicBool, Ordering};
use tauri::Emitter;
use tokio::sync::{mpsc, Mutex};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use url::Url;

// Import MIC_ACTIVE from lib.rs
use crate::MIC_ACTIVE;

// Global state for WS sender
static WS_SENDER: once_cell::sync::Lazy<Mutex<Option<mpsc::UnboundedSender<Message>>>> =
    once_cell::sync::Lazy::new(|| Mutex::new(None));

// Atomic flag to control the audio loop lifetime
static IS_RUNNING: AtomicBool = AtomicBool::new(false);

pub async fn start(agent_id: String, lang: String, token: String, app: tauri::AppHandle) -> Result<(), String> {
    if IS_RUNNING.load(Ordering::SeqCst) {
        return Err("Audio pipeline is already running".into());
    }
    IS_RUNNING.store(true, Ordering::SeqCst);

    // Default to dev backend, but can be overwritten by env var VITE_BACKEND_URL in future
    let mut ws_url = String::from("ws://127.0.0.1:8000/ws/live");
    if let Ok(url) = std::env::var("VITE_BACKEND_URL") {
        ws_url = url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/live";
    }

    let url_str = format!("{}?agent_id={}&lang={}&token={}", ws_url, agent_id, lang, token);
    let url = Url::parse(&url_str).map_err(|e| e.to_string())?;

    log::info!("Connecting to WebSocket: {} (token hidden)", ws_url);

    // 1. Connect WebSocket
    let (ws_stream, _) = connect_async(url).await.map_err(|e| e.to_string())?;
    use futures_util::{StreamExt, SinkExt};
    let (mut write, mut read) = ws_stream.split();

    log::info!("WebSocket Connected!");
    let _ = app.emit("audio_connected", ());

    let (tx_ws, mut rx_ws) = mpsc::unbounded_channel::<Message>();
    
    // Store transmitter globally to allow sending JSON control messages later
    *WS_SENDER.lock().await = Some(tx_ws.clone());

    // Send loop (Rust -> FastAPI)
    tokio::spawn(async move {
        while let Some(msg) = rx_ws.recv().await {
            if !IS_RUNNING.load(Ordering::SeqCst) {
                break;
            }
            if write.send(msg).await.is_err() {
                break;
            }
        }
        let _ = write.close().await;
    });

    // --- The non-Send scope ---
    // In order to keep cpal::Stream alive, they must not be moved into a spawned task (tokio or std::thread).
    // They must live in this function's block.
    // However, since audio::start needs to return so Tauri's command finishes,
    // we must do the streams initialization inside a dedicated native thread that blocks while IS_RUNNING is true.
    let app_clone = app.clone();
    
    std::thread::spawn(move || {
        use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
        let host = cpal::default_host();
        
        // 2. Setup Audio Hardware
        let input_device = match host.default_input_device() {
            Some(d) => d,
            None => return,
        };
        let output_device = match host.default_output_device() {
            Some(d) => d,
            None => return,
        };

        // We need 16kHz mono for input (Gemini req)
        let input_config = cpal::StreamConfig {
            channels: 1,
            sample_rate: cpal::SampleRate(16000),
            buffer_size: cpal::BufferSize::Default,
        };

        // We need 24kHz mono for output (Gemini response)
        let output_config = cpal::StreamConfig {
            channels: 1,
            sample_rate: cpal::SampleRate(24000),
            buffer_size: cpal::BufferSize::Default,
        };

        let tx_ws_clone = tx_ws.clone();
        
        // Create RingBuffer for Playback (Capacity for ~1 second of 24kHz f32 audio)
        let rb = ringbuf::HeapRb::<f32>::new(24000 * 2);
        let (mut prod, mut cons) = ringbuf::traits::Split::split(rb);

        // Spawn Input Stream
        let input_stream = input_device.build_input_stream(
            &input_config,
            move |data: &[f32], _: &_| {
                // Push-To-Talk / VAD simulation: only send if MIC_ACTIVE is true
                if MIC_ACTIVE.load(Ordering::SeqCst) {
                    // Convert f32 to PCM16 little-endian bytes for Gemini
                    let mut pcm16_bytes = Vec::with_capacity(data.len() * 2);
                    for &sample in data {
                        // scale f32 [-1.0, 1.0] to i16
                        let s_i16 = (sample * 32767.0).clamp(-32768.0, 32767.0) as i16;
                        pcm16_bytes.extend_from_slice(&s_i16.to_le_bytes());
                    }
                    let _ = tx_ws_clone.send(Message::Binary(pcm16_bytes.into()));
                }
            },
            move |err| {
                log::error!("Input stream error: {}", err);
            },
            None,
        ).unwrap();

        input_stream.play().unwrap();

        // Spawn Output Stream
        let output_stream = output_device.build_output_stream(
            &output_config,
            move |data: &mut [f32], _: &_| {
                for sample in data.iter_mut() {
                    *sample = ringbuf::traits::Consumer::try_pop(&mut cons).unwrap_or(0.0);
                }
            },
            move |err| {
                log::error!("Output stream error: {}", err);
            },
            None,
        ).unwrap();

        output_stream.play().unwrap();

        // Spawn async sub-task to listen WS and populate Playback buffer
        let app_sub = app_clone.clone();
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async move {
            use futures_util::StreamExt;
            while let Some(msg) = read.next().await {
                if !IS_RUNNING.load(Ordering::SeqCst) {
                    break;
                }

                match msg {
                    Ok(Message::Binary(bin)) => {
                        // Gemini returns 24kHz PCM16. Convert back to f32 for output.
                        let mut i = 0;
                        while i + 1 < bin.len() {
                            let sample_i16 = i16::from_le_bytes([bin[i], bin[i + 1]]);
                            let sample_f32 = (sample_i16 as f32) / 32768.0;
                            let _ = ringbuf::traits::Producer::try_push(&mut prod, sample_f32);
                            i += 2;
                        }
                    }
                    Ok(Message::Text(text)) => {
                        // It's a control message (like session_ready or transcript)
                        let _ = app_sub.emit("ws_message_received", text.to_string());
                    }
                    Ok(Message::Close(_)) | Err(_) => {
                        break;
                    }
                    _ => {}
                }
            }
        });

        // The thread ends, dropping the streams
        log::info!("Audio/WS thread finished");
        IS_RUNNING.store(false, Ordering::SeqCst);
        let _ = app_clone.emit("audio_disconnected", ());
    });

    Ok(())
}

pub async fn stop() -> Result<(), String> {
    stop_internal().await
}

async fn stop_internal() -> Result<(), String> {
    IS_RUNNING.store(false, Ordering::SeqCst);
    
    let mut sender_guard = WS_SENDER.lock().await;
    *sender_guard = None; // Drops sender, closing the WS send loop

    Ok(())
}

pub async fn send_ws_message(payload: String) -> Result<(), String> {
    let guard = WS_SENDER.lock().await;
    if let Some(sender) = guard.as_ref() {
        sender.send(Message::Text(payload.into())).map_err(|e| e.to_string())?;
        Ok(())
    } else {
        Err("WebSocket not active".into())
    }
}
