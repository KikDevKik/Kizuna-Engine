use base64::{Engine as _, engine::general_purpose::STANDARD};
use image::ImageOutputFormat;
use std::io::Cursor;
use xcap::Monitor;

#[tauri::command]
fn capture_screen() -> Result<String, String> {
    let monitors = Monitor::all().map_err(|e| e.to_string())?;
    let monitor = monitors.first().ok_or_else(|| "No monitor found".to_string())?;
    let image = monitor.capture_image().map_err(|e| e.to_string())?;
    let rgb = image::DynamicImage::ImageRgba8(image).to_rgb8();
    let mut buf = Cursor::new(Vec::new());
    rgb.write_to(&mut buf, ImageOutputFormat::Jpeg(80))
        .map_err(|e| e.to_string())?;
    Ok(STANDARD.encode(buf.into_inner()))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_opener::init())
    .invoke_handler(tauri::generate_handler![capture_screen])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
