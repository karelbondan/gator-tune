import requests
from discord.ext import commands

from utilities.classes.utilities import MusicUtils

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"


class Music:
    def __init__(
        self,
        bot: commands.Bot,
        id: str,
        title: str,
        creator: str,
        url: str,
        lyrics: str,
        source: str,
        duration: str,
        playlist_title="",
    ) -> None:
        self.id = id
        self.bot = bot
        self.title = title
        self.creator = creator
        self.duration = duration
        self.url = url
        self.lyrics = lyrics
        self.source = source
        self.playlist_title = playlist_title
        self.utils = MusicUtils()

    def _check(self):
        # thanks chatgpt lmoa
        # apparently endpoints that returns a streamable will make request 
        # download the whole shit first. makes sense though. here's where
        # the range header comes into play to save a shit ton of time.
        headers = {"User-Agent": USER_AGENT, "Range": "bytes=0-1023"}
        return requests.get(url=self.source, headers=headers)

    async def expired(self):
        """Check whether the streamable URL has expired"""
        req = await self.bot.loop.run_in_executor(None, self._check)
        return not req.ok

    async def refetch(self, check=True):
        """Refetch the streamable URL if it has expired"""
        expired = await self.expired() if check else True
        if expired:
            self.source = self.utils.stream(self.id)
