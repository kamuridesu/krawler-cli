import asyncio
from pathlib import Path

from src.crawler_downloader_cli.config import Config
from src.crawler_downloader_cli.utils import Progress, ProgressData, Request


class Downloder:
    def __init__(self, config: Config, data: dict[str, list], req: Request):
        self.config = config
        self.data = data
        self.request = req
        self.progress = Progress(True)
        self.progress.start()

        self.sem = asyncio.Semaphore(10)

        self.tasks: set[asyncio.Task] = set()

        self.done = []

    async def __download(self, url: str, folder: Path, pg: ProgressData):
        pg.status = "Downloading"
        async with self.sem:
            try:
                data = await self.request.get(url)
                target = folder / data.filename
                target.write_bytes(data.content)
                pg.status = "Done"
            except Exception:
                pg.status = "Failed"

    async def start(self):
        print()
        print(f"[INFO] Starting download")
        c = 1
        for k, v in self.data.items():
            target = Path(self.config.target) / k
            target.mkdir(exist_ok=True)
            for i in v:
                if i in self.done:
                    continue
                self.done.append(i)
                pg = self.progress.register(c)
                task = asyncio.create_task(self.__download(i, target, pg))
                self.tasks.add(task)
                c += 1
        await asyncio.gather(*self.tasks)
        print()
        print(f"[INFO] Done!")
