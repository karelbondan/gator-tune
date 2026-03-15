from __future__ import annotations

from typing import TYPE_CHECKING, cast

import requests
from aiohttp import ClientSession

from configs import API_KEY, SERVICE_URL, SERVICE_VER
from utilities.classes.types import Song

if TYPE_CHECKING:
    from main import GatorTune


class MusicService:
    def __init__(self, bot: GatorTune):
        self.bot = bot
        self.req_headers = {"X-API-Key": API_KEY}

    def search(self, query: str):
        url = "{}/{}/music/search?query={}".format(SERVICE_URL, SERVICE_VER, query)
        res = requests.get(url, headers=self.req_headers)
        body = res.json()
        if res.status_code != 200:
            raise RuntimeError(body)
        return cast(Song, body)

    async def stream(self, video_id: str):
        url = "{}/{}/music/?id={}".format(SERVICE_URL, SERVICE_VER, video_id)
        async with ClientSession() as session:
            async with session.get(url, headers=self.req_headers) as res:
                if res.status == 404:
                    raise LookupError(res.json())
                if res.status != 200:
                    raise RuntimeError(res.json())
                txt = await res.text()
                # fmt:off
                return txt.replace("\"", "") # <- this lost me two fucking hours holy fucking shit im losing myself over two fucking double quotes
                # fmt:on
