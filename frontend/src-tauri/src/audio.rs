use std::sync::atomic::{AtomicBool, Ordering};
use tauri::Emitter;
use tokio::sync::{mpsc, Mutex};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use url::Url;
use ringbuf::traits::Observer;

// Continuous audio stream (VAD server-side)

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

    // Default to production backend, but can be overwritten by env var VITE_BACKEND_URL in future
    let mut ws_url = String::from("wss://kizuna-engine-smdnfrav2a-an.a.run.app/ws/live");
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

        // Get supported default configs
        let input_config_supported = match input_device.default_input_config() {
            Ok(c) => c,
            Err(e) => {
                log::error!("Failed to get default input config: {}", e);
                return;
            }
        };
        let output_config_supported = match output_device.default_output_config() {
            Ok(c) => c,
            Err(e) => {
                log::error!("Failed to get default output config: {}", e);
                return;
            }
        };

        let input_config = input_config_supported.config();
        let in_channels = input_config.channels as usize;
        let in_sample_rate = input_config.sample_rate.0;

        let output_config = output_config_supported.config();
        let out_channels = output_config.channels as usize;
        let out_sample_rate = output_config.sample_rate.0;

        log::info!("Audio Default Configs - IN: {}Hz {}ch | OUT: {}Hz {}ch", in_sample_rate, in_channels, out_sample_rate, out_channels);

        let tx_ws_clone = tx_ws.clone();
        
        // Create RingBuffer for Playback (Capacity for ~1 second of out_sample_rate f32 audio)
        let rb = ringbuf::HeapRb::<f32>::new((out_sample_rate as usize) * 2);
        let (mut prod, mut cons) = ringbuf::traits::Split::split(rb);

        // Spawn Input Stream
        let input_stream = input_device.build_input_stream(
            &input_config,
            move |data: &[f32], _: &_| {
                // Stream continuously (VAD is handled server-side)
                {
                    // Convert multi-channel to mono
                    let mono_samples: Vec<f32> = data.chunks(in_channels).map(|chunk| {
                        chunk.iter().sum::<f32>() / in_channels as f32
                    }).collect();

                    // Resample native in_sample_rate to 16kHz
                    let out_len = (mono_samples.len() as f32 * 16000.0 / in_sample_rate as f32) as usize;
                    let mut pcm16_bytes = Vec::with_capacity(out_len * 2);

                    for i in 0..out_len {
                        let src_idx = (i as f32 * in_sample_rate as f32 / 16000.0) as usize;
                        if src_idx < mono_samples.len() {
                            let sample = mono_samples[src_idx];
                            // scale f32 [-1.0, 1.0] to i16
                            let s_i16 = (sample * 32767.0).clamp(-32768.0, 32767.0) as i16;
                            pcm16_bytes.extend_from_slice(&s_i16.to_le_bytes());
                        }
                    }

                    if !pcm16_bytes.is_empty() {
                        let _ = tx_ws_clone.send(Message::Binary(pcm16_bytes.into()));
                    }
                }
            },
            move |err| {
                log::error!("Input stream error: {}", err);
            },
            None,
        ).unwrap();

        input_stream.play().unwrap();

        // Spawn Output Stream
        // Jitter Buffer logic
        let mut frames_played = 0;
        let pcm_start_threshold = (out_sample_rate as f32 * 0.2) as usize; // ~200ms of audio
        
        let output_stream = output_device.build_output_stream(
            &output_config,
            move |data: &mut [f32], _: &_| {
                for frame in data.chunks_mut(out_channels) {
                    let play_sample = if frames_played < pcm_start_threshold {
                        // Delay playback until buffer accumulates (Jitter buffering)
                        // If we can peek that the producer has pushed enough, or just count what we pop.
                        // For simplicity, we just count how many we COULD pop versus waiting.
                        if cons.occupied_len() > pcm_start_threshold {
                            frames_played = pcm_start_threshold; // Trigger playback start
                            ringbuf::traits::Consumer::try_pop(&mut cons).unwrap_or(0.0)
                        } else {
                            0.0 // Silence while buffering
                        }
                    } else {
                        // Play normal
                        let s = ringbuf::traits::Consumer::try_pop(&mut cons).unwrap_or(0.0);
                        if s == 0.0 && cons.is_empty() {
                            // Reset jitter buffer if we starved
                            frames_played = 0;
                        }
                        s
                    };

                    for channel_sample in frame.iter_mut() {
                        *channel_sample = play_sample;
                    }
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
                        // Gemini returns 24kHz PCM16. Convert back to mono f32.
                        let mut mono_24k = Vec::new();
                        let mut i = 0;
                        while i + 1 < bin.len() {
                            let sample_i16 = i16::from_le_bytes([bin[i], bin[i + 1]]);
                            let sample_f32 = (sample_i16 as f32) / 32768.0;
                            mono_24k.push(sample_f32);
                            i += 2;
                        }

                        // Resample 24kHz -> out_sample_rate
                        // Resample 24kHz -> out_sample_rate (Linear Interpolation)
                        let out_len = (mono_24k.len() as f32 * out_sample_rate as f32 / 24000.0) as usize;
                        for i in 0..out_len {
                            let src_pos = i as f32 * 24000.0 / out_sample_rate as f32;
                            let src_idx = src_pos as usize;
                            let frac = src_pos - src_idx as f32;
                            let s0 = if src_idx < mono_24k.len() { mono_24k[src_idx] } else { 0.0 };
                            let s1 = if src_idx + 1 < mono_24k.len() { mono_24k[src_idx + 1] } else { s0 };
                            let resampled = s0 + frac * (s1 - s0);
                            
                            let _ = ringbuf::traits::Producer::try_push(&mut prod, resampled);
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
