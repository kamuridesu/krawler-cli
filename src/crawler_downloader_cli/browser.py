from playwright.async_api import async_playwright, Browser

from src.crawler_downloader_cli.abstract import BaseDriver


async def fetch_page(url: str, browser: Browser):
        page = await browser.new_page()
        await page.goto(url)
        content = await page.content()
        return content


class FirefoxDriver(BaseDriver):
    async def fetch_page(self, url: str) -> str:
        print("[INFO/Firefox] Fetching page " + url)
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=False)
            data = await fetch_page(url, browser)
            await browser.close()
            await p.stop()
        print("[INFO/Firefox] Returning data ")
        return data


class ChromiumDriver(BaseDriver):
    async def fetch_page(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            data = await fetch_page(url, browser)
            await browser.close()
            await p.stop()
        return data


def get_browser_driver(browser: str) -> BaseDriver | None:
    drivers: dict[str, BaseDriver] = {
        "firefox": FirefoxDriver(),
        "chormium": ChromiumDriver(),
    }

    return drivers.get(browser)
