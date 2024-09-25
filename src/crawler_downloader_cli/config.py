from dataclasses import dataclass
from pathlib import Path

import yaml

from src.crawler_downloader_cli.abstract import BaseDriver
from src.crawler_downloader_cli.browser import get_browser_driver

type StrOrPath = str | Path

ALLOWED_BROWSERS_LIST = ["chromium", "firefox", "disabled"]


@dataclass
class URL:
    url: str
    extensions: list[str]

    @classmethod
    def parse(cls, data: dict) -> "URL":
        kwargs = {}
        for field in URL.__dict__.get("__match_args__", []):
            value = data.get(field)
            kwargs[field] = value
        return URL(**kwargs)


@dataclass
class Config:
    urls: list[URL]
    target: str
    browser: BaseDriver | None

    @classmethod
    def parse(cls, data: dict) -> "Config":
        kwargs = {}
        for field in Config.__dict__.get("__match_args__", []):
            value: str | list[URL] | None | BaseDriver = data.get(field)
            if field == "urls" and value:
                value = [URL.parse(x) for x in value]
            if field == "browser":
                if isinstance(value, str):
                    if value not in ALLOWED_BROWSERS_LIST:
                        raise ValueError(
                            f"Browser '{value}' not supported! Allowed values are: "
                            + ", ".join(ALLOWED_BROWSERS_LIST)
                        )
                    value = get_browser_driver(value)
            kwargs[field] = value
        return Config(**kwargs)

    @staticmethod
    def load(filename: StrOrPath) -> "Config":
        with open(filename) as f:
            return Config.parse(yaml.safe_load(f))
