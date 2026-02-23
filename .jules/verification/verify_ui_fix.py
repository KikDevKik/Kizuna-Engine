
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})

        try:
            await page.goto("http://localhost:5173", timeout=10000)
            await page.wait_for_selector(".kizuna-engine-viewport", timeout=10000)
            await page.screenshot(path=".jules/verification/hud_fix_main.png")
            print("Screenshots captured successfully.")
        except Exception as e:
            print(f"Error: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
