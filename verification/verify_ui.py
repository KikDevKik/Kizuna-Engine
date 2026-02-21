from playwright.sync_api import sync_playwright, expect

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 720})

        try:
            print("Navigating to http://localhost:5173...")
            page.goto("http://localhost:5173", timeout=60000)

            # Wait for content to load. Since backend is down, we expect "NEW SOUL" card.
            print("Waiting for NEW SOUL card...")
            # We can select by text "FORGE NEW SOUL" which is inside the card
            page.wait_for_selector("text=FORGE NEW SOUL", timeout=10000)

            print("Taking roster screenshot...")
            page.screenshot(path="verification/ui_roster.png")

            # Check for System Logs
            print("Verifying System Logs...")
            expect(page.locator("text=SYS.LOG //")).to_be_visible()

            # Open Jules Sanctuary
            print("Opening Jules Sanctuary (Ctrl+Shift+P)...")
            page.keyboard.press("Control+Shift+P")

            # Wait for modal with new class
            print("Waiting for modal...")
            modal = page.locator(".shape-modal-shard")
            expect(modal).to_be_visible()

            print("Taking sanctuary screenshot...")
            page.screenshot(path="verification/ui_sanctuary.png")

            print("Verification complete!")

        except Exception as e:
            print(f"Error during verification: {e}")
            page.screenshot(path="verification/error.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    verify_ui()
