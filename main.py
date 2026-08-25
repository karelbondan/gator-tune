import glob
import importlib
import os
import tempfile
from os import path

from discord import Intents
from discord.ext import commands

import configs
from classes.database import Database
from utilities import strings
from utilities.bot_helper import init
from utilities.log_helper import log_info

prefix: str = configs.CONFIG["prefix"]


class GatorTune(commands.Bot):
    def __init__(self, command_prefix, *args, **kwargs):
        super().__init__(command_prefix=command_prefix, *args, **kwargs)  # noqa
        self.database = Database()
        self._commands()

    async def on_ready(self):
        # Clean up any leftover zombie files from a previous crash
        temp_dir = tempfile.gettempdir()
        search_pattern = os.path.join(temp_dir, "discord_ffmpeg_*.log")

        leftover_files = glob.glob(search_pattern)
        purged_count = 0

        for file_path in leftover_files:
            try:
                os.remove(file_path)
                purged_count += 1
            except OSError:
                pass

        if purged_count > 0:
            print(f"Clared {purged_count} ffmpeg log files from previous crash.")

    async def setup_hook(self):
        for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
            if filename.endswith(".py") and "__init__" not in filename:
                await self.load_extension(name=f"cogs.{filename[:-3]}")
        return await super().setup_hook()

    def _commands(self):
        @self.command()
        async def reload(ctx: commands.Context):
            importlib.reload(strings)
            if ctx.author.id != int(configs.OWNER):
                log_info("Reload invoked but not by owner id")
                return await ctx.send(strings.Gator.ERR_FORBD.format(configs.OWNER))

            for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
                if filename.endswith(".py") and "__init__" not in filename:
                    cog = filename[:-3]
                    await self.reload_extension(name=f"cogs.{cog}")
                    msg = f"`{strings.Gator.CNLG}: cog.{cog} extension successfully reloaded`"
                    await ctx.send(msg)
                    log_info(msg)

            # for the lols
            await ctx.send(strings.Gator.WHTF.format(configs.OWNER))


if __name__ == "__main__":
    if not configs.USE_SERVICE:
        # make the download folder
        if not os.path.isdir(configs.DOWNLOAD_LOC):
            os.mkdir(configs.DOWNLOAD_LOC)

        # trigger the authentication prompt
        if configs.USE_OAUTH:
            init()

    # run the bot
    bot = GatorTune(
        command_prefix=prefix, owner_id=configs.OWNER, intents=Intents.all()
    )
    bot.run(token=configs.TOKEN)
