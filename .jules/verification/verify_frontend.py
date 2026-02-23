from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Navigate to the app
        print("Navigating to app...")
        page.goto("http://localhost:5173/")

        # Wait for the app to load (checking for title or key element)
        print("Waiting for app to load...")
        page.wait_for_selector("text=KIZUNA") # Header text

        # Verify VisionPanel toggle button exists (top right)
        print("Checking VisionPanel...")
        # The VisionPanel is a fixed div at top-24 right-4 containing a button
        # We can look for the SVG icon inside it if needed, or just the button
        page.wait_for_selector("div.fixed.top-24.right-4 button")

        # Take a screenshot of the main view
        print("Taking main screenshot...")
        page.screenshot(path=".jules/verification/verification.png")

        # Try to open JulesSanctuary (Ctrl+Shift+P)
        print("Opening JulesSanctuary...")
        page.keyboard.press("Control+Shift+P")

        # Wait for modal to appear
        # The modal has text "NEURAL LAB // JULES ACCESS"
        page.wait_for_selector("text=NEURAL LAB // JULES ACCESS", timeout=5000)

        # Take a screenshot of the modal
        print("Taking modal screenshot...")
        page.screenshot(path=".jules/verification/verification_modal.png")

        print("Verification successful!")

    except Exception as e:
        print(f"Verification failed: {e}")
        page.screenshot(path=".jules/verification/error.png")
        raise e
    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
