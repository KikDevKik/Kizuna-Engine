import os
import sys
import time
from playwright.sync_api import sync_playwright

def verify_jules_sanctuary():
    print("Starting verification for Jules Sanctuary...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Listen for console logs and errors
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))

        url = "http://localhost:5173"
        print(f"Navigating to {url}...")
        try:
            page.goto(url)
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            print("Make sure the frontend server is running.")
            return

        # Wait for initial load
        try:
            page.wait_for_selector(".kizuna-core-container", timeout=10000)
            print("Initial load complete.")
        except Exception as e:
            print("Error waiting for core container:", e)
            page.screenshot(path="frontend/verification/screenshots/error_load.png")
            return

        # Trigger Hotkey: Ctrl+Shift+J
        print("Triggering hotkey Ctrl+Shift+J...")
        # Note: on Mac usually Meta+Shift+J, on Windows/Linux Ctrl+Shift+J.
        # Playwright's 'Control' maps to Ctrl.
        page.keyboard.press("Control+Shift+J")

        # Wait for Sanctuary to appear
        # We look for the unique text "NEURAL LAB // JULES ACCESS"
        try:
            page.wait_for_selector("text=NEURAL LAB // JULES ACCESS", timeout=5000)
            print("SUCCESS: Jules Sanctuary overlay appeared.")
        except Exception as e:
            print("FAILURE: Jules Sanctuary did not appear.")
            print(e)
            page.screenshot(path="frontend/verification/screenshots/error_sanctuary.png")
            browser.close()
            return

        # Check for Video Element
        video_visible = page.is_visible("video")
        if video_visible:
            print("SUCCESS: Video element found.")
        else:
            print("WARNING: Video element not found or not visible.")

        # Take screenshot
        os.makedirs("frontend/verification/screenshots", exist_ok=True)
        screenshot_path = "frontend/verification/screenshots/jules_sanctuary_verified.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    verify_jules_sanctuary()
