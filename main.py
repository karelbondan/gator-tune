import importlib
import os
from os import path

from discord import Intents
from discord.ext import commands

import configs
import utilities.strings as strings
from utilities.classes.database import Database
from utilities.classes.utilities import log_info

prefix: str = configs.CONFIG["prefix"]


class GatorTune(commands.Bot):
    def __init__(self, command_prefix, *args, **kwargs):
        super().__init__(command_prefix=command_prefix, *args, **kwargs)
        self.database = Database()
        self._commands()

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
                    await self.reload_extension(name="cogs.{}".format(cog))
                    msg = "`{}: cog.{} extension successfully reloaded`".format(
                        strings.Gator.CNLG, cog
                    )
                    await ctx.send(msg)
                    log_info(msg)

            # for the lols
            await ctx.send(strings.Gator.WHTF.format(configs.OWNER))


if __name__ == "__main__":
    bot = GatorTune(
        command_prefix=prefix, owner_id=configs.OWNER, intents=Intents.all()
    )
    bot.run(token=configs.TOKEN)
