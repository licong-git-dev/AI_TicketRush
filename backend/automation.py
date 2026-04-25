from playwright.async_api import async_playwright, Browser, Page

class BrowserManager:
    """
    A singleton class to manage the Playwright browser instance.
    """
    def __init__(self):
        self.browser: Browser | None = None
        self.page: Page | None = None
        self._playwright = None

    async def launch(self):
        """
        Launches the browser. We run it in non-headless mode so the user can interact with it.
        """
        if self.browser:
            print("Browser already launched.")
            return

        print("Launching browser...")
        self._playwright = await async_playwright().start()
        # Using chromium, not in headless mode so we can see the UI.
        self.browser = await self._playwright.chromium.launch(headless=False, slow_mo=50)
        self.page = await self.browser.new_page()
        print("Browser launched successfully.")

    async def go_to(self, url: str):
        """
        Navigates the browser page to a specific URL.
        """
        if not self.page:
            raise Exception("Page is not initialized. Call launch() first.")
        print(f"Navigating to {url}...")
        await self.page.goto(url)
        print(f"Navigated to {url}")

    async def close(self):
        """
        Closes the browser and stops the Playwright instance.
        """
        if not self.browser:
            return

        print("Closing browser...")
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        print("Browser closed.")

# Create a single instance that will be used across the entire application.
browser_manager = BrowserManager() 