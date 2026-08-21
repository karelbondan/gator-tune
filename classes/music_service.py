from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING, cast

import requests
from aiohttp import ClientSession

from classes.exceptions import ServiceError
from classes.types import Song
from configs import API_KEY, SERVICE_URL, SERVICE_VER

if TYPE_CHECKING:
    from main import GatorTune


class MusicService:
    def __init__(self, bot: GatorTune):
        self.bot = bot
        self.req_headers = {"X-API-Key": API_KEY}

    def search(self, query: str):
        url = f"{SERVICE_URL}/{SERVICE_VER}/music/search?query={query}"
        req = requests.get(url, headers=self.req_headers)

        # accommodate for errors first
        res: str | dict
        try:
            res = req.json()
        except JSONDecodeError:
            txt = req.text
            res = txt if len(txt.split()) < 40 else req.reason
        if req.status_code != 200:
            raise ServiceError(f"HTTP {req.status_code}: {res!s}")

        return cast(Song, res)

    async def stream(self, video_id: str):
        url = f"{SERVICE_URL}/{SERVICE_VER}/music/?id={video_id}"
        async with (
            ClientSession() as session,
            session.get(url, headers=self.req_headers) as req,
        ):
            if not req.ok:
                try:
                    res = await req.json()
                except JSONDecodeError:
                    txt = await req.text()
                    res = txt if len(txt.split()) < 40 else req.reason
                raise ServiceError(f"HTTP {req.status}: {res!s}")

            txt = await req.text()

            # fmt:off
            return txt.replace("\"", "") # <- this lost me two fucking hours holy fucking shit im losing myself over two fucking double quotes
            # fmt:on
