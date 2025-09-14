import requests

import utilities.classes.types as types
from utilities.classes.utilities import MusicUtils

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"


class Music(types.Music):
    def __init__(
        self,
        id: str,
        title: str,
        creator: str,
        url: str,
        lyrics: str,
        source: str,
        duration: str,
        playlist_title="",
    ) -> None:
        super().__init__(
            id, title, creator, url, lyrics, source, duration, playlist_title
        )
        self.utils = MusicUtils()

    async def expired(self):
        """Check whether the streamable URL has expired"""
        headers = {"User-Agent": USER_AGENT}
        req = requests.get(url=self.source, headers=headers)
        return not req.ok

    async def refetch(self, check=True):
        """Refetch the streamable URL if it has expired"""
        expired = await self.expired() if check else True
        if expired:
            self.source = self.utils.stream(self.source)
