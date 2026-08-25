from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

from discord import Message

if TYPE_CHECKING:
    from classes.selection import Selection
    from model.music import Music


class State(TypedDict):
    voice_channel: int | None
    text_channel: int | None
    now_playing: str
    queue: list[Music]
    repeat: Literal["on", "off", "all"]
    active_selection: Selection | None
    message_cache: dict[int, Message]


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
    url: str | None
    title: str
    cover: str | None
    queue: list[PlaylistQueue] | None
    duration: str
    playlist_title: str | None


class Commands(TypedDict):
    play: list[str]
    pause: list[str]
    resume: list[str]
    repeat: list[str]
    stop: list[str]
    clear: list[str]
    leave: list[str]
    skip: list[str]
    remove: list[str]
    now_playing: list[str]
    queue: list[str]
    lyrics: list[str]
    choose: list[str]


class Config(TypedDict):
    status: str
    prefix: str
    leave_seconds: int
    node_script: str
    time_limit: int
    max_retries: int
    retry_delay: int
    choose_timeout: int
    commands: Commands
