from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from discord import Message
from discord.ext.commands import Context

if TYPE_CHECKING:
    from asyncio import Task

    from classes.types import Song


class Selection:
    """Music selection session object. Context is the message context sent by the original requester"""

    def __init__(
        self,
        songs: list[Song],
        context: Context,
        expiry: float = time.monotonic() + 60,
    ) -> None:
        self.context = context
        self.songs = songs
        self.message: Message | None = None
        self.expiry = expiry
        self.page = 1
        self.items_per_page = 5  # also acts as offset calculation
        self.total_page = math.ceil(len(self.songs) / self.items_per_page)
        self.timeout_task: Task | None = None
        # emoji 1 - 5
        # self.index_emojis = ["1\u20e3", "2\u20e3", "3\u20e3", "4\u20e3", "5\u20e3"]
        self.index_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    def get_paginated(self):
        start = self.items_per_page * (self.page - 1)
        end_calc = start + self.items_per_page
        end = end_calc if end_calc < len(self.songs) else -1
        return self.songs[self.items_per_page * (self.page - 1) : end]

    def get_number_emojis(self):
        paginated = self.get_paginated()
        return self.index_emojis[: len(paginated)]

    def next(self):
        """
        Returns True if successful. Useful for deciding whether the
        action involving this should be continued or not
        """
        if self.page < self.total_page:
            self.page += 1
            return True
        return False

    def prev(self):
        """
        Returns True if successful. Useful for deciding whether the
        action involving this should be continued or not
        """
        if self.page > 1:
            self.page -= 1
            return True
        return False

    def kill(self):
        if self.timeout_task:
            self.timeout_task.cancel()
