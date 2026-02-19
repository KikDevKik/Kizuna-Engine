from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Mock getUserMedia to prevent errors
        page.add_init_script("""
            navigator.mediaDevices.getUserMedia = async () => {
                return new MediaStream();
            };
        """)

        print("Navigating to http://localhost:5173")
        try:
            page.goto("http://localhost:5173", timeout=60000)
        except Exception as e:
            print(f"Error navigating: {e}")
            browser.close()
            return

        # Wait for the main title
        try:
            page.wait_for_selector("text=KIZUNA", timeout=10000)
            page.wait_for_selector("text=ENGINE", timeout=10000)
        except Exception as e:
            print(f"Timeout waiting for selectors: {e}")
            page.screenshot(path="frontend/verification/error.png")
            browser.close()
            return

        # Wait for Core View to be stable (initial animation)
        page.wait_for_timeout(2000)

        print("Taking Core View screenshot...")
        page.screenshot(path="frontend/verification/core_view.png")

        # Click Agent Roster
        print("Clicking Agent Roster...")
        try:
            page.click("text=AGENT ROSTER")
        except Exception as e:
             print(f"Error clicking Agent Roster: {e}")

        # Wait for transition
        page.wait_for_timeout(2000)

        print("Taking Roster View screenshot...")
        page.screenshot(path="frontend/verification/roster_view.png")

        browser.close()

if __name__ == "__main__":
    run()
