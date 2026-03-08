use std::sync::atomic::{AtomicBool, Ordering};
use tauri::{Emitter,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, RunEvent, WindowEvent,
};
use tauri_plugin_global_shortcut::{Code, Modifiers, Shortcut, ShortcutState};
use base64::{Engine as _, engine::general_purpose::STANDARD};
use image::codecs::jpeg::JpegEncoder;
use std::io::Cursor;
use xcap::Monitor;

#[tauri::command]
fn capture_screen() -> Result<String, String> {
    let monitors = Monitor::all().map_err(|e| e.to_string())?;
    let monitor = monitors.first().ok_or_else(|| "No monitor found".to_string())?;
    let image = monitor.capture_image().map_err(|e| e.to_string())?;
    let rgb = image::DynamicImage::ImageRgba8(image).to_rgb8();
    let mut buf = Cursor::new(Vec::new());
    let mut encoder = JpegEncoder::new_with_quality(&mut buf, 80);
    encoder.encode_image(&rgb).map_err(|e| e.to_string())?;
    Ok(STANDARD.encode(buf.into_inner()))
}

// Estado global del micrófono PTT — accesible desde Rust y frontend via evento
static MIC_ACTIVE: AtomicBool = AtomicBool::new(false);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // Plugins preexistentes e invocación de comandos
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![capture_screen])
        // Plugin de logs y setup de tray / shortcuts
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // --- SYSTEM TRAY ---
            let show = MenuItem::with_id(app, "show", "Abrir Kizuna", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Cerrar", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &quit])?;

            let _ = app.remove_tray_by_id("kizuna-tray");

            TrayIconBuilder::with_id("kizuna-tray")
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .tooltip("Kizuna Engine")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "quit" => {
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    // Click izquierdo en el ícono = abrir ventana
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            // --- PUSH-TO-TALK GLOBAL (Ctrl+Space) ---
            let handle = app.handle().clone();
            app.handle()
                .plugin(
                    tauri_plugin_global_shortcut::Builder::new()
                        .with_handler(move |_app, shortcut, event| {
                            let ptt = Shortcut::new(Some(Modifiers::CONTROL), Code::Space);
                            if shortcut == &ptt {
                                match event.state() {
                                    ShortcutState::Pressed => {
                                        MIC_ACTIVE.store(true, Ordering::SeqCst);
                                        // Notificar al frontend via evento Tauri
                                        if let Some(window) =
                                            handle.get_webview_window("main")
                                        {
                                            let _ = window.emit("ptt-start", ());
                                        }
                                    }
                                    ShortcutState::Released => {
                                        MIC_ACTIVE.store(false, Ordering::SeqCst);
                                        if let Some(window) =
                                            handle.get_webview_window("main")
                                        {
                                            let _ = window.emit("ptt-stop", ());
                                        }
                                    }
                                }
                            }
                        })
                        .build(),
                )?;

            Ok(())
        })
        // Plugin de notificaciones
        .plugin(tauri_plugin_notification::init())
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        // --- SURVIVE CLOSE: ventana se oculta, proceso no muere ---
        .run(|app_handle, event| {
            if let RunEvent::WindowEvent {
                label,
                event: WindowEvent::CloseRequested { api, .. },
                ..
            } = event
            {
                if let Some(window) = app_handle.get_webview_window(&label) {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
        });
}
