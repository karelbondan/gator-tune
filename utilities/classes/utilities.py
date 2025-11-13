from __future__ import annotations

import asyncio
import json
import re
import signal
import time
from os import kill, path
from time import strftime
from typing import TYPE_CHECKING, Dict, Tuple

import requests
from bs4 import BeautifulSoup
from discord import FFmpegOpusAudio
from pytubefix import Stream, YouTube

import configs
import utilities.strings as strings

if TYPE_CHECKING:
    from main import GatorTune
    from utilities.classes.types import Song

CONFIG = configs.CONFIG


def _format_tab(log_type: str):
    # 9 is the total length from start to before
    # the log msg, e.g. INFO     something
    return " {}{}".format(log_type, " " * (9 - len(log_type)))


def log_info(log: str):
    print("{}{}{}".format(strftime("%Y-%m-%d %H:%M:%S"), _format_tab("INFO"), log))


def log_warn(log: str):
    print("{}{}{}".format(strftime("%Y-%m-%d %H:%M:%S"), _format_tab("WARN"), log))


def log_error(log: str):
    print("{}{}{}".format(strftime("%Y-%m-%d %H:%M:%S"), _format_tab("ERROR"), log))


class MusicUtils:
    def __init__(self, bot: GatorTune):
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k -vbr constrained",
        }
        self.bot = bot

    def ffmpeg(self, song: str) -> FFmpegOpusAudio:
        return FFmpegOpusAudio(
            source=song,
            before_options=self.FFMPEG_OPTIONS["before_options"],
            options=self.FFMPEG_OPTIONS["options"],
        )

    def search(self, song: str) -> Song:
        # check if song is a yt link
        yt, url = self._find_link(query=song)
        if url and yt:
            return {
                "id": yt.video_id,
                "url": url.url,
                "title": yt.title,
                "queue": None,
                "duration": ".".join(map(str, divmod(yt.length, 60))),
                "playlist_title": None,
            }
        # search youtube
        response = requests.get(url=configs.URL + song, headers=configs.HEADERS)
        # get json response
        videos = self._result(response=response)
        with open(
            path.join(configs.ROOT_DIR, "test", "out", "search_result.txt"), "w"
        ) as search_out:
            search_out.write(json.dumps(videos))
        # actually get the list of result
        # fmt:off
        assert videos is not None
        videos = videos["contents"] \
            ["twoColumnSearchResultsRenderer"] \
            ["primaryContents"] \
            ["sectionListRenderer"]["contents"]
        # fmt:on
        # apparently yt also includes "adSlotRenderer" in the first index so yeah
        is_adv: dict = videos[0]["itemSectionRenderer"]["contents"][0]
        if list(is_adv.keys())[0] == "adSlotRenderer":
            videos = videos[1]["itemSectionRenderer"]["contents"]
        else:
            videos = videos[0]["itemSectionRenderer"]["contents"]

        # and get the first one
        # apparently yt includes "didYouMeanRenderer" if it thinks there's a typo in the query
        # also try to search for the first valid song for 10 times, if fails then just fail
        video_id = video_title = video_duration = ""
        for idx, songs in enumerate(videos):
            assert isinstance(songs, Dict)
            if idx > 10:
                break
            try:
                first_result = songs["videoRenderer"]
                video_id: str = first_result["videoId"]
                video_title: str = first_result["title"]["runs"][0]["text"]
                video_duration: str = first_result["lengthText"]["simpleText"]
                break
            except KeyError:
                continue

        return {
            "id": video_id,
            "url": None,
            "title": video_title,
            "queue": None,
            "duration": video_duration,
            "playlist_title": None,
        }

    def playlist(self, id: str) -> Song:
        # get data
        response = requests.get(url=configs.PLAYLIST + id, headers=configs.HEADERS)
        # parse data
        videos = self._result(response=response)
        assert videos is not None

        with open(
            path.join(configs.ROOT_DIR, "test", "out", "playlist_video_json.txt"), "w"
        ) as search_out:
            search_out.write(json.dumps(videos))
        # get the list
        # fmt:off
        try:
            playlist_title = videos["header"]["pageHeaderRenderer"]["pageTitle"]
        except KeyError: 
            playlist_title = videos["header"]["playlistHeaderRenderer"]["title"]["simpleText"]
        videos = videos["contents"] \
            ["twoColumnBrowseResultsRenderer"]["tabs"][0] \
            ["tabRenderer"]["content"]["sectionListRenderer"] \
            ["contents"][0]["itemSectionRenderer"]["contents"][0] \
            ["playlistVideoListRenderer"]["contents"]
        # fmt:on
        # get the first one, return the rest
        video_id = video_title = video_duration = ""
        queue = []
        for idx, video in enumerate(videos):
            this = video["playlistVideoRenderer"]
            id = this["videoId"]
            title = this["title"]["runs"][0]["text"]
            duration = this["lengthText"]["simpleText"]

            if idx == 0:
                video_id = id
                video_title = title
                video_duration = duration
            else:
                queue.append({"id": id, "title": title, "duration": duration})

        return {
            "id": video_id,
            "url": None,
            "title": video_title,
            "queue": queue,
            "duration": video_duration,
            "playlist_title": playlist_title,
        }

    async def token(self):
        """Refreshes the visitor data and po token"""
        await self._potoken()

    def _result(self, response: requests.Response):
        # parse response using bs4 and get search result
        soup = BeautifulSoup(response.content.decode("utf-8"), features="html5lib")
        # the index of the script that contains the data varies by time.
        # at the time of this writing it was 23. for loop is better to reduce
        # the script breaking from changes made by yt
        scripts = soup.find_all("script")
        for details in scripts:
            if "ytInitialData" in str(details):
                data = re.findall(
                    r"(?<=var ytInitialData = ).+(?=;</script>)",
                    str(details),
                )
                return json.loads(data[0])

    def _youtube(self, video_id: str) -> Tuple[YouTube, Stream | None]:
        if not path.exists("./token.json"):
            asyncio.run_coroutine_threadsafe(self._potoken(), self.bot.loop).result()
        youtube = YouTube(
            url=configs.YT + video_id, use_po_token=True, token_file="./token.json"
        )
        return youtube, youtube.streams.get_audio_only()

    def _find_link(
        self, query: str
    ) -> Tuple[YouTube, Stream | None] | Tuple[None, None]:
        """Check if the given query is a youtube link, if not then return nothing"""
        yt_url_regex = (
            r"(https?:\/\/([\w\.]{1,256})?youtu(\.)?be(\.com)?/(watch\?v=)?)([\w-]+)"
        )
        try:
            video_id = re.findall(yt_url_regex, query)[0][-1]
            return self._youtube(video_id=video_id)
        except IndexError:
            return None, None

    def stream(self, video_id: str) -> str:
        youtube = self._youtube(video_id)[1]
        assert youtube is not None
        return youtube.url

    # thanks a lot chatgpt lol
    async def _potoken(self) -> Tuple[str, str]:
        """Async migrate function to generate token using one-shot.js"""
        retries = 0
        output = {}
        while True:
            log_info(strings.Log.TOK_START)
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                "node",
                CONFIG["node_script"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            pid = process.pid
            log_info(strings.Log.TOK_SUMMONED.format(pid))

            try:
                # Wait for process to finish or timeout
                await asyncio.wait_for(process.wait(), timeout=CONFIG["time_limit"])

                # read stdout - moved from old code
                # has to be beneath the asyncio wait to let the timeout work
                assert process.stdout is not None
                async for line in process.stdout:
                    decoded = line.decode("utf-8").strip().replace(",", "")
                    try:
                        k, v = decoded.split(":")
                        key = k.strip().replace("poToken", "po_token")
                        output[key] = eval(v.strip())
                    except Exception:
                        pass

                with open("./token.json", "w", encoding="utf-8") as token:
                    json.dump(output, token, indent=4)

                elapsed = time.time() - start_time
                log_info(strings.Log.TOK_EXITED_0.format(pid, elapsed))
                break
            except asyncio.TimeoutError:
                # Process exceeded time limit
                log_error(strings.Log.TOK_TIMEOUT.format(pid, CONFIG["time_limit"]))
                process.terminate()

                try:
                    await asyncio.wait_for(process.wait(), timeout=CONFIG["time_limit"])
                except asyncio.TimeoutError:
                    log_warn(strings.Log.TOK_EXITED_1.format(pid))
                    kill(pid, signal.SIGKILL)

                retries += 1
                elapsed = time.time() - start_time
                msg = strings.Log.TOK_EXCEED.format(
                    pid, elapsed, retries, CONFIG["max_retries"]
                )
                log_warn(msg)

                if retries >= CONFIG["max_retries"]:
                    log_warn(strings.Log.TOK_RETMAX)
                    break

                log_info(strings.Log.TOK_RETRY.format(CONFIG["retry_delay"]))
                await asyncio.sleep(CONFIG["retry_delay"])

        log_info(strings.Log.TOK_DONE)
        if len(output.keys()) < 1:
            raise RuntimeError(strings.Log.TOK_FAIL)
        return tuple(output.values())
