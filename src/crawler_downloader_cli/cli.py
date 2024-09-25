import argparse
from pathlib import Path

from src.crawler_downloader_cli.config import Config


def init():
    parser = argparse.ArgumentParser(
        prog="Spider Downloader",
        description="Crawl websites and try to download media.",
    )
    parser.add_argument("--config", default="", required=False)
    args = parser.parse_args()

    config_file = "crawl.yaml"

    if args.config:
        config_file = args.config

    config_file = Path(config_file)
    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file {config_file.name} does not exists in {config_file.parent}"
        )

    return Config.load(config_file)
