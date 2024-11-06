from discord import Intents
from discord.ext import commands
from os import path
import configs
import os
from utilities.utilities import log_info

prefix: str = configs.CONFIG["prefix"]


class GatorTune(commands.Bot):
    def __init__(self, command_prefix, *args, **kwargs):
        super().__init__(command_prefix=command_prefix, *args, **kwargs)
        self._commands()

    async def setup_hook(self):
        for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
            if filename.endswith(".py") and "__init__" not in filename:
                await bot.load_extension(name=f"cogs.{filename[:-3]}")
        return await super().setup_hook()

    def _commands(self):
        @self.command()
        async def reload(ctx: commands.Context):
            # fmt:off
            if ctx.author.id != int(configs.OWNER):
                log_info("Reload invoked but not by owner id"); return
            # fmt:on

            for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
                if filename.endswith(".py") and "__init__" not in filename:
                    cog = filename[:-3]
                    await bot.reload_extension(name="cogs.{}".format(cog))
                    msg = "cog.{} extension successfully reloaded".format(cog)
                    # fmt:off
                    await ctx.send(msg); log_info(msg)
                    # fmt:on


if __name__ == "__main__":
    bot = GatorTune(
        command_prefix=prefix, owner_id=configs.OWNER, intents=Intents.all()
    )
    bot.run(token=configs.TOKEN)
