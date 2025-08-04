from typing import Dict

from discord import Guild

from utilities.classes.types import State


class Database:
    def __init__(self) -> None:
        self.database: Dict[int, State] = {}

    def push(self, guild_id: int):
        """Instantiates a new database record of a newly joined guild in the main thread"""
        self.database[guild_id] = {
            "voice_channel": None,
            "text_channel": None,
            "now_playing": "",
            "queue": [],
            "repeat": "off",
        }
        return self.database[guild_id]

    def get(self, guild_id: int):
        database = self.database.get(guild_id)
        if not database:
            database = self.push(guild_id)
        return database
    
    def update(self, guild: Guild, data: State):
        self.database[guild.id] = data

    def remove(self, guild: Guild):
        """Remove guild data from the in-memory database"""
        self.database.pop(guild.id, {})
