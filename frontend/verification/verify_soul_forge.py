import time
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()

    # Mock Agents List
    page.route("**/api/agents/", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": "test-1", "name": "KIZUNA-TEST", "role": "GUARDIAN", "systemStatus": "ONLINE"}]'
    ))

    # Mock Ritual Start
    request_count = 0
    def handle_ritual(route):
        nonlocal request_count
        request_count += 1
        if request_count == 1:
            route.fulfill(
                status=200,
                content_type="application/json",
                body='{"is_complete": false, "message": "The Void gazes back. State your desire."}'
            )
        else:
            route.fulfill(
                 status=200,
                 content_type="application/json",
                 body='{"is_complete": false, "message": "Why do you fear solitude?"}'
            )

    page.route("**/api/agents/ritual", handle_ritual)

    try:
        page.goto("http://localhost:5173")

        # Wait for Roster
        page.wait_for_selector("text=KIZUNA-TEST", timeout=10000)

        # Navigate to Create Card
        page.click("text=NEXT >")
        time.sleep(2)

        if not page.is_visible("text=INITIALIZE"):
             page.click("text=NEXT >")
             time.sleep(2)

        page.click("text=INITIALIZE")

        # Wait for Modal
        page.wait_for_selector("text=SOUL FORGE", timeout=5000)

        # Check for Initial Message
        # Force finish typing by clicking the text area
        page.click("text=SOUL FORGE") # Click header to focus, maybe click body?
        # The TypewriterText is inside the message div.
        # We can try to click the container.

        time.sleep(1)

        # Check text
        content = page.content()
        if "The Void gazes back" in content:
            print("Found 'The Void gazes back'")
        elif "Te Void" in content:
            print("Found 'Te Void' (Typo detected?)")
        else:
            print("Initial message NOT found in content.")

        page.wait_for_selector("text=The Void gazes back", timeout=5000)

        # Check input exists
        page.wait_for_selector("input[placeholder='Enter your response...']", timeout=2000)

        # Type something
        page.fill("input[placeholder='Enter your response...']", "I want a loyal companion.")

        # Click Send
        page.click("button[type='submit']")

        # Wait for new message
        page.wait_for_selector("text=Why do you fear solitude?", timeout=5000)

        page.screenshot(path="frontend/verification/soul_forge_verified.png")
        print("Verification Successful: Soul Forge Modal interactive.")

    except Exception as e:
        page.screenshot(path="frontend/verification/soul_forge_error_2.png")
        print(f"Verification Failed: {e}")
        raise e
    finally:
        browser.close()

with sync_playwright() as p:
    run(p)
