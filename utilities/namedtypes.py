from typing import TypedDict, Literal
from discord import VoiceClient
from discord.ext import commands


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
    clear_queue_on_leave: bool
    now_playing: str
    paused: bool
    queue: list[Queue]
    repeat: Literal["on", "off", "all"]
    voice_channel: None | VoiceClient
    text_channel: None | commands.Context


class Db(TypedDict):
    guild_id: State
