from typing import Literal, TypedDict, Optional


class Music:
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
        self.id = id
        self.title = title
        self.creator = creator
        self.duration = duration
        self.url = url
        self.lyrics = lyrics
        self.source = source
        self.playlist_title = playlist_title

    async def expired(self) -> bool:
        return True

    async def refetch(self, check=True):
        pass


class Queue(TypedDict):
    id: str
    title: str
    duration: str
    source: str


class PlaylistQueue(TypedDict):
    id: str
    title: str
    duration: str


class State(TypedDict):
    voice_channel: int | None
    text_channel: int | None
    now_playing: str
    queue: list[Music]
    repeat: Literal["on", "off", "all"]


class Database(TypedDict):
    guild_id: State


class Song(TypedDict):
    id: str
    url: Optional[str]
    title: str
    queue: Optional[list[PlaylistQueue]]
    duration: str
    playlist_title: Optional[str]
