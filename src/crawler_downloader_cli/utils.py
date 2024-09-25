import asyncio
import http.cookies
from dataclasses import dataclass
from random import randint
import sys
from typing import Literal

import filetype
from aiohttp import ClientSession, ClientTimeout

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 8_9_2; like Mac OS X) AppleWebKit/602.17 (KHTML, like Gecko)  Chrome/50.0.3965.134 Mobile Safari/603.2"
}


@dataclass
class FileInfo:
    filename: str
    content: bytes
    mime: str
    size: int
    origin: str = ""


@dataclass
class ProgressData:
    id: int
    progress: float = 0
    status: Literal["Failed"] | Literal["Done"] | Literal["Downloading"] | None = None

    def update(self, count: int, total_size: int):
        self.progress = 100 * count / float(total_size)


class Progress:
    def __init__(self,  for_tasks=False):
        self.progress_data: list[ProgressData] = []
        self.task: asyncio.Task | None = None
        self.for_tasks = for_tasks

    def register(self, id: int):
        pd = ProgressData(id)
        self.progress_data.append(pd)
        return pd

    async def generate(self):
        body = ""
        if not self.for_tasks:
            for file in self.progress_data:
                if file.progress == 100:
                    continue
                if file.status is None:
                    body += f"File {file.id}: {file.progress:.1f}%\n"
                    continue
                body += f"File {file.id}: {file.status}"
        else:
            count = len(self.progress_data)
            for task in self.progress_data:
                if task.status == "Done":
                    count -= 1
            body = f"Tasks: [{count}/{len(self.progress_data)}]"
        sys.stdout.write(f"[PROGRESS] " + body)
        sys.stdout.flush()

    async def __start(self):
        timeout = 10 if not self.for_tasks else 1
        while True:
            await self.generate()
            await asyncio.sleep(timeout)

    def start(self):
        self.task = asyncio.Task(self.__start())

    async def finish(self):
        await self.generate()
        if self.task:
            self.task.cancel()


def generate_random_id(digits: int = 6):
    _id = ""
    for _ in range(digits):
        _id += str(randint(0, 9))
    return _id


class Request:
    def __init__(self):
        self.session = ClientSession(timeout=ClientTimeout(600))

    async def __aenter__(self, *args, **kwargs):
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.session.close()

    async def close(self):
        await self.session.close()

    def set_cookies(self, cookies: list[dict]):
        for cookie in cookies:
            try:
                self.session.cookie_jar.update_cookies(cookie)
            except http.cookies.CookieError:
                # print(f"[ERROR] Could not set cookie {cookie}. Skipping")
                ...

    async def get(self, url: str, progress: ProgressData | None = None):
        async with self.session.get(url, headers=DEFAULT_HEADERS) as response:
            if response.status != 200:
                # print(f"[WARN] Erro fetching URL {url}, status is {response.status}")
                raise TypeError("Can't fetch URL")
            filename = f"{generate_random_id()}"
            size = 0
            ctype = ""
            content = b""
            if "Content-Disposition" in response.headers:
                filename = (
                    response.headers["Content-Disposition"]
                    .split("filename=")[1]
                    .strip('"')
                )
            if "Content-Length" in response.headers:
                size = int(response.headers["Content-Length"])
            if progress:
                progress.status = "Downloading"
            content = await response.read()
            if progress:
                progress.status = "Done"
            if "Content-Type" in response.headers:
                ctype = response.headers.get("Content-Type", "").split("/")[1]
                if ";" in ctype:
                    ctype = ctype.split(";")[0]
            ext = filetype.guess_extension(content)
            mime = filetype.guess_mime(content)
            if mime is None:
                mime = ""
            if not ext:
                ext = ""
            return FileInfo(
                filename
                + (
                    ("." + ext)
                    if ext is None and not filename.endswith(ext)
                    else ("." + ctype) if not filename.endswith(ctype) else ""
                ),
                content,
                mime,
                size,
            )
