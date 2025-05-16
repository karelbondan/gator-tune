import os
import yaml
from dotenv import load_dotenv
from os import path

load_dotenv(override=True)

# definitions
ROOT_DIR = path.dirname(path.abspath(__file__))
TAB = " " * int(os.getenv("TAB_AMT"))

# for song search
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
}
URL = "https://www.youtube.com/results?search_query="
YT = "https://youtu.be/"
PLAYLIST = "https://www.youtube.com/playlist?list="

# bot
TOKEN = os.getenv("TOKEN")
OWNER = os.getenv("OWNER")

with open(path.join(ROOT_DIR, "config.yml"), "r", encoding="utf-8") as config:
    CONFIG = yaml.load(config, Loader=yaml.SafeLoader)
