from playwright.async_api import Browser, async_playwright

from src.crawler_downloader_cli.abstract import BaseDriver


async def fetch_page(url: str, browser: Browser):
    try:
        page = await browser.new_page(ignore_https_errors=True)
        await page.goto(url)
        content = await page.content()
        return content
    except Exception:
        return ""


class FirefoxDriver(BaseDriver):
    async def fetch_page(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            data = await fetch_page(url, browser)
            await browser.close()
            await p.stop()
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
        "chromium": ChromiumDriver(),
    }

    return drivers.get(browser)
