import asyncio
from urllib.parse import urlparse

from src.crawler_downloader_cli.config import URL, Config
from src.crawler_downloader_cli.parser import fetch_links, parse_find_url, parse_url
from src.crawler_downloader_cli.utils import FileInfo, Progress, ProgressData, Request


class Fetcher:
    def __init__(self, config: Config):
        self.config = config
        self.request = Request()
        self.visited_urls = set()
        self.content = {}
        self.browser_driver = self.config.browser
        self.progress = Progress(for_tasks=True)
        self.progress.start()

        self.semaphore = asyncio.Semaphore(5)

    async def __aenter__(self, *args, **kwargs):
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.request.close()

    def is_same_domain(self, origin: str, url: str) -> bool:
        return urlparse(origin).netloc == urlparse(url).netloc

    async def fetch_page(self, url: str, _id=0) -> FileInfo | None:
        progress = ProgressData(1)
        try:
            return await self.request.get(url, progress=progress)
        except Exception as e:
            return None

    async def fetch_browser_page(self, url: str, domain, extensions, pg):
        if self.browser_driver:
            async with self.semaphore:
                browser_content = await self.browser_driver.fetch_page(url)
                await self.progress.generate()
                matches = parse_find_url(browser_content, extensions)
                if matches:
                    self.content[domain].extend(matches)

    async def crawl_url(self, url: str, extensions: list[str], _id=0):
        url = url.strip()
        if url in self.visited_urls:
            return
        self.visited_urls.add(url)

        pg = self.progress.register(_id)

        pg.status = "Downloading"
        file_info = await self.fetch_page(url, _id)
        if not file_info:
            pg.status = "Failed"
            return

        domain = urlparse(url).netloc
        if domain not in self.content:
            self.content[domain] = []

        if file_info.filename.endswith(".html") and "html" in str(file_info.content):
            links = fetch_links(file_info.content, url)
            tasks = []
            for i, link in enumerate(links, 1):
                if self.is_same_domain(url, link):
                    tasks.append(self.crawl_url(link, extensions, _id + i))
            await asyncio.gather(*tasks)
        matches = parse_find_url(file_info.content, extensions)
        if matches:
            self.content[domain].extend([parse_url(url, x) for x in matches])
            pg.status = "Done"
        else:
            await self.fetch_browser_page(url, domain, extensions, pg)
        pg.status = "Done"

    async def start(self):
        tasks = []
        for url_obj in self.config.urls:
            tasks.append(self.crawl_url(url_obj.url, url_obj.extensions))
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.progress.finish()
