import time
import sys
from playwright.sync_api import sync_playwright

def benchmark_vision():
    print("Starting Vision Benchmark...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
        )
        page = browser.new_page()

        # Inject spy on document.createElement
        page.add_init_script("""
            window._canvasCount = 0;
            const originalCreateElement = document.createElement;
            document.createElement = function(tagName, options) {
                if (tagName && tagName.toLowerCase() === 'canvas') {
                    window._canvasCount++;
                }
                return originalCreateElement.apply(document, arguments);
            };
        """)

        url = "http://localhost:5173"
        print(f"Navigating to {url}...")
        try:
            page.goto(url)
        except Exception as e:
            print(f"Error navigating: {e}")
            return

        # Wait for load
        try:
            page.wait_for_selector(".kizuna-core-container, .kizuna-shard-nav-btn", timeout=10000)
            print("App loaded.")
        except Exception as e:
            print("Timeout waiting for app load.")
            page.screenshot(path="frontend/verification/screenshots/error_load_bench.png")
            return

        # 1. Select Agent (Roster View)
        print("Selecting Agent...")
        try:
            # Wait for Roster to load agents. "INITIATE LINK" means a valid agent is focused.
            # "INITIALIZE" means 'New Soul' is focused.
            # We assume 'Kizuna' is first and focused.
            page.wait_for_selector("text=INITIATE LINK", timeout=5000)
            page.click("text=INITIATE LINK")
            print("Agent selected.")
        except:
            print("Could not find 'INITIATE LINK' on Roster. Maybe 'New Soul' is focused?")
            page.screenshot(path="frontend/verification/screenshots/error_roster_bench.png")
            return

        # 2. Connect (Core View)
        print("Connecting to Backend...")
        try:
            # Wait for Core View to appear
            page.wait_for_selector("text=CORE VIEW", timeout=5000)

            # The button in Core View also says "INITIATE LINK" initially
            # Use a specific selector or just text again (Playwright finds visible ones)
            # Ensure we click the one in the main area, not the header nav (Header nav says "CORE VIEW" and "AGENT ROSTER")
            # The button has "INITIATE LINK" text inside.

            # Wait for the specific button
            core_connect_btn = page.locator("button.kizuna-shard-btn-wrapper").filter(has_text="INITIATE LINK")
            core_connect_btn.click()

            # Wait for connection (Text changes to TERMINATE)
            page.wait_for_selector("text=TERMINATE", timeout=10000)
            print("Connected.")
        except Exception as e:
            print(f"Connection failed: {e}")
            page.screenshot(path="frontend/verification/screenshots/error_connect_bench.png")
            return

        # 3. Open Jules Sanctuary
        print("Opening Jules Sanctuary (Ctrl+Shift+P)...")
        page.keyboard.press("Control+Shift+P")

        # Wait for Sanctuary
        try:
            page.wait_for_selector("text=NEURAL LAB // JULES ACCESS", timeout=5000)
            print("Sanctuary open.")
        except:
            print("Sanctuary failed to open.")
            page.screenshot(path="frontend/verification/screenshots/error_sanctuary_bench.png")
            return

        # 4. Wait for Video ready and Button enabled
        time.sleep(2)
        capture_btn = page.get_by_role("button", name="CAPTURE FRAME")

        if capture_btn.is_disabled():
            print("Capture button still disabled.")
            # Check why
            status = page.locator("div.space-y-2").inner_text()
            print(f"Status Panel: {status}")
            page.screenshot(path="frontend/verification/screenshots/error_camera_bench_connected.png")
            return

        # 5. Benchmark
        print("Clicking Capture 5 times...")
        # Reset count if needed? No, we just count total.
        # But verify spy is working?
        current_count = page.evaluate("window._canvasCount")
        print(f"Canvas count before loop: {current_count}")

        for i in range(5):
            capture_btn.click()
            time.sleep(0.5)

        final_count = page.evaluate("window._canvasCount")
        delta = final_count - current_count
        print(f"BENCHMARK RESULT: Canvas creations during capture loop = {delta}")
        print(f"Total Canvas creations = {final_count}")

        browser.close()

if __name__ == "__main__":
    benchmark_vision()
