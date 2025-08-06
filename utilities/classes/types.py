from typing import Literal, TypedDict, Optional


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
    queue: list[Queue]
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
