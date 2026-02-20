import time
from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    print("Navigating to frontend...")
    # Assume default Vite port 5173
    try:
        page.goto("http://localhost:5173", timeout=10000)
    except Exception as e:
        print(f"Failed to load page: {e}")
        # Try waiting a bit more or checking if it's running
        time.sleep(5)
        try:
            page.goto("http://localhost:5173")
        except:
            print("Frontend not ready?")
            browser.close()
            return

    # Switch to Agent Roster View
    print("Switching to Agent Roster...")
    try:
        page.get_by_text("AGENT ROSTER").click()
    except Exception as e:
        print(f"Failed to click AGENT ROSTER: {e}")
        page.screenshot(path="verification/error_nav.png")
        browser.close()
        return

    # Wait for Agents to load
    print("Waiting for agents to load...")
    try:
        # Check for Kizuna card (Name) - wait longer for fetch
        expect(page.get_by_role("heading", name="Kizuna", exact=True)).to_be_visible(timeout=10000)
        print("Kizuna card visible.")
    except Exception as e:
        print(f"Kizuna card not found: {e}")
        page.screenshot(path="verification/error_load.png")
        browser.close()
        return

    # Screenshot initial state
    page.screenshot(path="verification/initial_roster.png")
    print("Screenshot saved: initial_roster.png")

    # Navigate to "Create New" card
    print("Looking for FORGE NEW SOUL...")

    found_forge = False

    # Check if currently visible
    if page.get_by_text("FORGE NEW SOUL").is_visible():
        found_forge = True
        print("FORGE NEW SOUL is visible.")
    else:
        # Rotate until found
        print("Rotating carousel...")
        for _ in range(10): # Max 10 rotations
            if page.get_by_text("FORGE NEW SOUL").is_visible():
                found_forge = True
                break
            # Click Next
            try:
                # The Next button is inside AgentRoster
                # It might be an arrow or text "NEXT >"
                page.get_by_text("NEXT >").click(timeout=1000)
                time.sleep(0.5) # Wait for animation
            except:
                print("Could not click NEXT")
                break

    if not found_forge:
        print("Could not find FORGE NEW SOUL card.")
        page.screenshot(path="verification/error_find_forge.png")
        # Proceeding anyway to see if we can force it or if logic is just hidden

    # Click the card to select it (if not already selected)
    # In the carousel, usually the center one is selected.
    # If we stopped when it is visible, it should be selectable.
    try:
        page.get_by_text("FORGE NEW SOUL").click()
        time.sleep(1) # Wait for selection state update
    except:
        pass

    # Click "INITIALIZE" button (which appears when create card is active)
    print("Attempting to click INITIALIZE...")
    try:
        # Wait for button to say "INITIALIZE"
        # The button might be the same "INITIATE LINK" button but changed text?
        # No, in AgentRoster.tsx there is likely a specific button for this action
        # Let's look for text "INITIALIZE" inside a button

        # Note: If the carousel didn't rotate correctly, this might fail.
        # We can try forcing the click if we find the button
        btn = page.get_by_role("button", name="INITIALIZE")
        if btn.is_visible():
            btn.click()
            print("Clicked INITIALIZE button.")
        else:
             print("INITIALIZE button not visible. attempting to find it via text...")
             page.get_by_text("INITIALIZE").click()
             print("Clicked INITIALIZE text.")

    except Exception as e:
        print(f"Failed to click INITIALIZE: {e}")
        page.screenshot(path="verification/error_click_init.png")

    # Check Modal Open
    print("Checking for Modal...")
    try:
        expect(page.get_by_text("SOUL FORGE PROTOCOL")).to_be_visible(timeout=5000)
        print("Modal opened.")
    except:
        print("Modal did not open.")
        page.screenshot(path="verification/error_modal.png")
        browser.close()
        return

    # Fill Form
    print("Filling form...")
    # Use specific locators if placeholders are vague, but based on code they seemed unique
    page.get_by_placeholder("e.g. KIZUNA-02").fill("TEST-SOUL-" + str(int(time.time())))
    page.get_by_placeholder("e.g. TACTICAL SUPPORT").fill("VERIFICATION UNIT")
    page.get_by_placeholder("Define the soul's behavior, constraints, and personality...").fill("You are a test unit created by automation.")

    page.screenshot(path="verification/modal_filled.png")

    # Submit
    print("Submitting...")
    page.get_by_text("INITIALIZE SOUL").click()

    # Wait for modal to close (or check for success)
    # Expect modal to disappear
    try:
        expect(page.get_by_text("SOUL FORGE PROTOCOL")).not_to_be_visible(timeout=5000)
        print("Modal closed.")
    except:
        print("Modal did not close automatically.")
        page.screenshot(path="verification/error_modal_close.png")

    # Check for new agent in roster
    print("Verifying new agent in roster...")
    # It might take a moment to fetch/render
    time.sleep(2)

    # We need to find "TEST-SOUL"
    # It might require rotation
    found_agent = False
    if page.get_by_text("VERIFICATION UNIT").is_visible():
         found_agent = True
    else:
        for _ in range(10):
            if page.get_by_text("VERIFICATION UNIT").is_visible():
                found_agent = True
                break
            page.get_by_text("NEXT >").click()
            time.sleep(0.5)

    if found_agent:
        print("New agent VERIFICATION UNIT found!")
    else:
        print("Could not find new agent.")

    page.screenshot(path="verification/final_roster.png")
    print("Verification complete.")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
