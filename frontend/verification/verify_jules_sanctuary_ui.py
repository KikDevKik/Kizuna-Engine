from playwright.sync_api import sync_playwright, expect
import time

def verify_jules_sanctuary():
    with sync_playwright() as p:
        # Launch browser (headless for CI/sandbox)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            permissions=['camera', 'microphone'] # Grant permissions
        )
        page = context.new_page()

        try:
            # Navigate to the app
            print("Navigating to http://localhost:5173/...")
            page.goto("http://localhost:5173/")

            # Wait for main UI to load (check for specific text)
            print("Waiting for app to load...")
            expect(page.get_by_text("KIZUNAENGINE")).to_be_visible(timeout=10000)

            # Take initial screenshot
            page.screenshot(path="frontend/verification/before_sanctuary.png")

            # Press Control+Shift+P
            print("Pressing Control+Shift+P...")
            page.keyboard.press("Control+Shift+P")

            # Wait for Sanctuary to appear
            print("Waiting for Neural Lab overlay...")
            sanctuary_header = page.get_by_text("NEURAL LAB // JULES ACCESS")
            expect(sanctuary_header).to_be_visible(timeout=5000)

            # Verify video element exists
            video = page.locator("video")
            expect(video).to_be_visible()

            # Verify buttons
            capture_btn = page.get_by_role("button", name="CAPTURE FRAME")
            expect(capture_btn).to_be_visible()

            sync_btn = page.get_by_role("button", name="AUTO SYNC (2s)")
            expect(sync_btn).to_be_visible()

            # Take screenshot of the open sanctuary
            print("Taking screenshot...")
            page.screenshot(path="frontend/verification/jules_sanctuary_open.png")
            print("Verification successful!")

        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="frontend/verification/failure.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    verify_jules_sanctuary()
