from discord import FFmpegPCMAudio
from bs4 import BeautifulSoup
from typing import Tuple
from pytubefix import YouTube
from os import path
from time import strftime
import requests
import configs
import re
import json
import os

def _format_tab(log_type: str):
    # 9 is the total length from start to before 
    # the log msg, e.g. INFO     something
    return " {}{}".format(log_type, " " * (9 - len(log_type)))

def log_info(log: str):
    print("{}{}{}".format(strftime('%Y-%m-%d %H:%M:%S'), _format_tab("INFO"), log))

def log_warn(log: str):
    print("{}{}{}".format(strftime('%Y-%m-%d %H:%M:%S'), _format_tab("WARN"), log))
    
def log_error(log: str):
    print("{}{}{}".format(strftime('%Y-%m-%d %H:%M:%S'), _format_tab("ERROR"), log))
    
    
class Music:
    def __init__(self):
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

    def ffmpeg(self, song: str) -> FFmpegPCMAudio:
        return FFmpegPCMAudio(source=song, options=self.FFMPEG_OPTIONS)

    def search(self, song: str) -> Tuple[str]:
        # search youtube
        response = requests.get(url=configs.URL + song, headers=configs.HEADERS)

        # parse response using bs4 and get search result
        soup = BeautifulSoup(response.content, features="html5lib")
        videos = {}
        # the index of the script that contains the data varies by time.
        # at the time of this writing it was 23. for loop is better to reduce
        # the script breaking from changes made by yt
        scripts = soup.find_all("script")
        for details in scripts:
            if "ytInitialData" in str(details):
                data = re.findall(r"(?<=var ytInitialData = ).+(?=;</script>)", str(details))
                videos = json.loads(data[0])
                break

        # actually get the list of result
        videos = videos["contents"]["twoColumnSearchResultsRenderer"][
            "primaryContents"
        ]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]

        # and get the first one
        first_result = videos[0]["videoRenderer"]
        video_id = first_result["videoId"]
        video_title = first_result['title']['runs'][0]['text']

        return (video_id, video_title)
    
    def download(self, video_id: str) -> str:
        # yt config
        youtube = YouTube(url=configs.YT + video_id)
        config = youtube.streams.get_audio_only()
        
        # output, download, rename
        output = path.join(configs.ROOT_DIR, "audios")
        downld = config.download(output_path=output, mp3=True)
        rename = path.join(output, video_id, ".mp3")
        os.rename(downld, rename)
        
        return video_id
