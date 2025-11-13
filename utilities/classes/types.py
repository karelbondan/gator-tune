from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Optional, TypedDict

if TYPE_CHECKING:
    from utilities.classes.music import Music


class State(TypedDict):
    voice_channel: int | None
    text_channel: int | None
    now_playing: str
    queue: list[Music]
    repeat: Literal["on", "off", "all"]


class Queue(TypedDict):
    id: str
    title: str
    duration: str
    source: str


class PlaylistQueue(TypedDict):
    id: str
    title: str
    duration: str


class Song(TypedDict):
    id: str
    url: Optional[str]
    title: str
    queue: Optional[list[PlaylistQueue]]
    duration: str
    playlist_title: Optional[str]


class Commands(TypedDict):
    play: List[str]
    pause: List[str]
    resume: List[str]
    repeat: List[str]
    stop: List[str]
    clear: List[str]
    leave: List[str]
    skip: List[str]
    remove: List[str]
    now_playing: List[str]
    queue: List[str]
    lyrics: List[str]


class Config(TypedDict):
    status: str
    prefix: str
    leave_seconds: int
    node_script: str
    time_limit: int
    max_retries: int
    retry_delay: int
    commands: Commands
