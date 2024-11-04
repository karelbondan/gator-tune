from typing import TypedDict
from discord import VoiceClient


class State(TypedDict):
    clear_queue_on_leave: bool
    now_playing: str
    paused: bool
    queue: list[str]
    voice_channel: None | VoiceClient


class Db(TypedDict):
    guild_id: State
