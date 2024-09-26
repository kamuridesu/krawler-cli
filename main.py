import asyncio

from crawler_downloader_cli.cli import init
from crawler_downloader_cli.download import Downloder
from crawler_downloader_cli.fetch import Fetcher
from src.crawler_downloader_cli.config import Config
from src.crawler_downloader_cli.utils import Progress


async def main():
    config = init()

    async with Fetcher(config) as fetcher:
        await fetcher.start()
        # print(fetcher.content)
        dl = Downloder(config, fetcher.content, fetcher.request)
        await dl.start()


if __name__ == "__main__":
    asyncio.run(main())
