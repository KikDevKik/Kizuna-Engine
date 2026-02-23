from playwright.sync_api import sync_playwright

def capture_initial(page):
    print("Navigating to http://localhost:5173...")
    page.goto("http://localhost:5173")

    # Wait for the agent cards to appear
    print("Waiting for .agent-card-glass...")
    try:
        page.wait_for_selector(".agent-card-glass", timeout=10000)
    except Exception as e:
        print(f"Error waiting for selector: {e}")
        # Take a screenshot anyway to see what happened
        page.screenshot(path=".jules/verification/initial_error.png")
        return

    # Allow animations to settle
    page.wait_for_timeout(2000)

    print("Taking screenshot...")
    page.screenshot(path=".jules/verification/initial_state.png", full_page=True)
    print("Screenshot saved to .jules/verification/initial_state.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Emulate a typical desktop resolution
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        try:
            capture_initial(page)
        finally:
            browser.close()
