import asyncio
from crawler_downloader_cli.fetch import Fetcher
from src.crawler_downloader_cli.utils import Progress
from src.crawler_downloader_cli.config import Config


async def main():
    progress = Progress()
    config = Config.load("example.yaml")  # Load the configuration

    async with Fetcher(config) as fetcher:
        await fetcher.start(progress)
        print(fetcher.content)


if __name__ == "__main__":
    asyncio.run(main())
