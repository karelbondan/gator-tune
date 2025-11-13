from __future__ import annotations

from os import getenv, path
from typing import TYPE_CHECKING, cast

import yaml
from dotenv import load_dotenv

# thanks a ton https://stackoverflow.com/a/39757388
if TYPE_CHECKING:
    from utilities.classes.types import Config

load_dotenv(override=True)

# definitions
ROOT_DIR = path.dirname(path.abspath(__file__))
TAB = " " * int(cast(str, getenv("TAB_AMT")))

# for song search
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
}
URL = "https://www.youtube.com/results?search_query="
YT = "https://youtu.be/"
PLAYLIST = "https://www.youtube.com/playlist?list="

# bot
TOKEN = cast(str, getenv("TOKEN"))
OWNER = cast(int, getenv("OWNER"))

# for generate token
NODE_SCRIPT = "utilities/generator/examples/one-shot.js"
TIME_LIMIT = 3  # seconds before killing
MAX_RETRIES = 5  # max retries if timeout occurs
RETRY_DELAY = 1  # seconds before retrying

with open(path.join(ROOT_DIR, "config.yml"), "r", encoding="utf-8") as config:
    CONFIG: Config = yaml.load(config, Loader=yaml.SafeLoader)
