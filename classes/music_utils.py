from __future__ import annotations

import asyncio
import json
import re
import signal
import time
from os import kill, path
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup
from pytubefix import Stream, YouTube

import configs
from classes.audio import Audio
from classes.exceptions import TokenGenerationFailure
from classes.types import Song
from utilities import strings
from utilities.log_helper import CONFIG, log_error, log_info, log_warn

if TYPE_CHECKING:
    from classes.selection import Selection
    from main import GatorTune


class MusicUtils:
    """This utility service is used if service is not used"""

    def __init__(self, bot: GatorTune):
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k -vbr constrained",
        }
        self.bot = bot

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

    def _youtube(self, video_id: str) -> tuple[YouTube, Stream | None]:
        if not path.exists("./token.json"):
            asyncio.run_coroutine_threadsafe(self._potoken(), self.bot.loop).result()
        if configs.USE_OAUTH:
            youtube = YouTube(url=configs.YT + video_id, use_oauth=True)
        else:
            youtube = YouTube(
                url=configs.YT + video_id, use_po_token=True, token_file="./token.json"
            )
        return youtube, youtube.streams.get_audio_only()

    def _find_link(
        self, query: str
    ) -> tuple[YouTube, Stream | None] | tuple[None, None]:
        """Check if the given query is a youtube link, if not then return nothing"""
        yt_url_regex = (
            r"(https?:\/\/([\w\.]{1,256})?youtu(\.)?be(\.com)?/(watch\?v=)?)([\w-]+)"
        )
        try:
            video_id = re.findall(yt_url_regex, query)[0][-1]
            return self._youtube(video_id=video_id)
        except IndexError:
            return None, None

    # thanks a lot chatgpt lol
    async def _potoken(self) -> tuple[str, str]:
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
                    except Exception:  # noqa
                        pass

                with open("./token.json", "w", encoding="utf-8") as token:  # noqa
                    json.dump(output, token, indent=4)

                elapsed = time.time() - start_time
                log_info(strings.Log.TOK_EXITED_0.format(pid, elapsed))
                break
            except TimeoutError:
                # Process exceeded time limit
                log_error(strings.Log.TOK_TIMEOUT.format(pid, CONFIG["time_limit"]))
                process.terminate()

                try:
                    await asyncio.wait_for(process.wait(), timeout=CONFIG["time_limit"])
                except TimeoutError:
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
            raise TokenGenerationFailure(strings.Log.TOK_FAIL)
        return tuple(output.values())

    async def token(self):
        """Refreshes the visitor data and po token"""
        await self._potoken()

    def find_id(self, query: str):
        """Check if the given query is a youtube link, if not then return nothing"""
        try:
            return re.findall(strings.Regexes.YT_URL, query)[0][-1]
        except IndexError:
            return None

    def ffmpeg(self, song: str) -> Audio:
        return Audio(
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
                "cover": yt.thumbnail_url,
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
        # next(iter)) -> get the first key of the dict
        if next(iter(is_adv)) == "adSlotRenderer":
            videos = videos[1]["itemSectionRenderer"]["contents"]
        else:
            videos = videos[0]["itemSectionRenderer"]["contents"]

        # and get the first one
        # apparently yt includes "didYouMeanRenderer" if it thinks there's a typo in the query
        # also try to search for the first valid song for 10 times, if fails then just fail
        video_id = video_title = video_duration = ""
        for idx, songs in enumerate(videos):
            assert isinstance(songs, dict)
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
            "cover": None,
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
            "cover": None,
        }

    def stream(self, video_id: str) -> str:
        fetch = self._youtube(video_id)
        yt = fetch[0]
        audio = fetch[1]
        audio_file = f"{configs.DOWNLOAD_LOC}/{yt.video_id}.m4a"

        # download the song, skip if already downloaded before
        if not path.isfile(audio_file):
            audio = yt.streams.get_audio_only()
            assert audio
            audio.download(
                filename=f"{video_id}.m4a",
                output_path=configs.DOWNLOAD_LOC,
            )

        return audio_file

    async def create_timeout(self, selection: Selection, guild_id: int):
        try:
            msg = selection.message
            await asyncio.sleep(selection.expire_seconds)

            if not msg:
                return

            tasks = [msg.clear_reactions(), msg.edit(content=strings.Gator.CHOOSE_EXP)]
            await asyncio.gather(*tasks)

            db = self.bot.database.get(guild_id)

            # clear active selection for the current guild
            db["active_selection"] = None

            # delete msg cache
            del db["message_cache"][msg.id]

        except asyncio.CancelledError:
            pass
