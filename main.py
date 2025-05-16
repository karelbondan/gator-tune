from discord import Intents, Guild
from discord.ext import commands
from os import path
from utilities.utilities import log_info
import utilities.namedtypes as namedtypes
import utilities.strings as strings
import configs
import os

prefix: str = configs.CONFIG["prefix"]


class GatorTune(commands.Bot):
    def __init__(self, command_prefix, *args, **kwargs):
        super().__init__(command_prefix=command_prefix, *args, **kwargs)
        self.db: namedtypes.Db = {}
        self._commands()

    async def setup_hook(self):
        for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
            if filename.endswith(".py") and "__init__" not in filename:
                await self.load_extension(name=f"cogs.{filename[:-3]}")
        return await super().setup_hook()

    def add_to_db(self, guild: Guild):
        """Instantiates a new database record of a newly joined guild in the main thread"""
        if guild.id not in self.db:
            self.db[guild.id] = {
                "clear_queue_on_leave": False,
                "now_playing": "",
                "paused": False,
                "queue": [],
                "repeat": "off",
                "voice_channel": None,
                "text_channel": None,
            }

    def _commands(self):
        @self.command()
        async def reload(ctx: commands.Context):
            # fmt:off
            if ctx.author.id != int(configs.OWNER):
                await ctx.send(strings.Gator.ERR_FORBD.format(configs.OWNER))
                log_info("Reload invoked but not by owner id"); return
            # fmt:on

            for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
                if filename.endswith(".py") and "__init__" not in filename:
                    cog = filename[:-3]
                    await self.reload_extension(name="cogs.{}".format(cog))
                    msg = "`{}: cog.{} extension successfully reloaded`".format(
                        strings.Gator.CNLG, cog
                    )
                    # fmt:off
                    await ctx.send(msg); log_info(msg)
                    # fmt:on

            # for the lols
            await ctx.send(strings.Gator.WHTF.format(configs.OWNER))


if __name__ == "__main__":
    bot = GatorTune(
        command_prefix=prefix, owner_id=configs.OWNER, intents=Intents.all()
    )
    bot.run(token=configs.TOKEN)
