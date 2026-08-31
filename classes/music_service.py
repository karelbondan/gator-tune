from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING, cast

import requests
from aiohttp import ClientResponse, ClientSession

from classes.exceptions import ServiceError
from classes.types import Song
from configs import API_KEY, SERVICE_URL, SERVICE_VER

if TYPE_CHECKING:
    from main import GatorTune


class MusicService:
    def __init__(self, bot: GatorTune):
        self.bot = bot
        self.req_headers = {"X-API-Key": API_KEY}

    def _parse_response(self, req: requests.Response):
        """For sync: requests lib"""
        # accommodate for errors first
        res: str | dict
        try:
            res = req.json()
        except JSONDecodeError:
            txt = req.text
            res = txt if len(txt.split()) < 40 else req.reason
        if not req.ok:
            raise ServiceError(f"HTTP {req.status_code}: {res!s}")

        return res

    async def _parse_response_async(self, req: ClientResponse):
        """For async: aiohttp lib"""
        if not req.ok:
            try:
                res = await req.json()
            except JSONDecodeError:
                txt = await req.text()
                res = txt if len(txt.split()) < 40 else req.reason
            raise ServiceError(f"HTTP {req.status}: {res!s}")
        return req

    def search(self, query: str):
        """Returns the first result"""
        url = f"{SERVICE_URL}/{SERVICE_VER}/music/search?query={query}"
        req = requests.get(url, headers=self.req_headers)
        res = self._parse_response(req)

        return cast(Song, res)

    async def choose(self, query: str):
        """Returns multiple search results"""
        url = f"{SERVICE_URL}/{SERVICE_VER}/music/batch?query={query}"
        async with (
            ClientSession() as session,
            session.get(url, headers=self.req_headers) as req,
        ):
            res = await self._parse_response_async(req)
            return cast(list[Song], await res.json())

    async def info(self, url_or_id: str):
        """Returns the song info"""
        url = f"{SERVICE_URL}/{SERVICE_VER}/music/info?id_or_url={url_or_id}"
        async with (
            ClientSession() as session,
            session.get(url, headers=self.req_headers) as req,
        ):
            res = await self._parse_response_async(req)
            return cast(Song, await res.json())

    async def stream(self, video_id: str):
        url = f"{SERVICE_URL}/{SERVICE_VER}/music/?id={video_id}"
        async with (
            ClientSession() as session,
            session.get(url, headers=self.req_headers) as req,
        ):
            res = await self._parse_response_async(req)
            txt = await res.text()
            # fmt:off
            return txt.replace("\"", "") # <- this lost me two fucking hours holy fucking shit im losing myself over two fucking double quotes
            # fmt:on
