import asyncio
from urllib.parse import urlparse
from src.crawler_downloader_cli.parser import parse_find_url, fetch_links
from src.crawler_downloader_cli.utils import FileInfo, Progress, ProgressData, Request
from src.crawler_downloader_cli.config import Config, URL


class Fetcher:
    def __init__(self, config: Config):
        self.config = config
        self.request = Request()
        self.visited_urls = set()
        self.content = {}
        self.browser_driver = self.config.browser
        self.progress = Progress(for_tasks=True)
        self.progress.start()

        self.to_fetch_in_browser = []

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
            # print(f"[ERROR/{_id}] Failed to fetch {url}: {e}")
            return None

    async def fetch_browser_page(self, url: str, domain, extensions, _id=0):
        if self.browser_driver:
            # print(f"[INFO/{_id}] Fetching {url} via browser...")
            browser_content = await self.browser_driver.fetch_page(url)
            await self.progress.generate()
            matches = parse_find_url(browser_content, extensions)
            if matches:
                self.content[domain].extend(matches)

    async def crawl_url(self, url: str, extensions: list[str], progress: Progress, _id=0):
        url = url.strip()
        if url in self.visited_urls:
            return
        self.visited_urls.add(url)

        pg = self.progress.register(_id)

        pg.status = "Downloading"
        file_info = await self.fetch_page(url, _id)
        if not file_info:
            return

        domain = urlparse(url).netloc
        if domain not in self.content:
            self.content[domain] = []

        if file_info.filename.endswith(".html") and "html" in str(file_info.content):
            links = fetch_links(file_info.content, url)
            tasks = []
            acc = _id
            for link in links:
                acc += 1
                if self.is_same_domain(url, link):
                    tasks.append(self.crawl_url(link, extensions, progress, acc))
            # print(f"[INFO/{_id}] Waiting for tasks to finish")
            await asyncio.gather(*tasks)
            # print(f"[INFO/{_id}] Finished")
        matches = parse_find_url(file_info.content, extensions)
        if matches:
            self.content[domain].extend(matches)
        else:
            # print(f"[INFO/{_id}] Starting Browser Call")
            # await self.fetch_browser_page(url, domain, extensions, _id)
            # # print(f"[INFO/{_id}] Finished Browser Call")
            self.to_fetch_in_browser.append((url, domain, extensions, _id))
                
        pg.status = "Done"

    async def start(self, progress: Progress):
        tasks = []
        for url_obj in self.config.urls:
            tasks.append(self.crawl_url(url_obj.url, url_obj.extensions, progress))
        print(f"[INFO] Last One Waiting for tasks to finish")
        await asyncio.gather(*tasks)
        await self.fetch_browser_page()
