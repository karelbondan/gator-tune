from typing import Literal
from discord import Message, Intents, utils, FFmpegPCMAudio
from discord.ext import commands
from os import path
import configs
import utilities.strings as strings
import os


prefix: str = configs.CONFIG["prefix"]
# bot = commands.Bot(prefix, intents=Intents.all())


class GatorTune(commands.Bot):
    def __init__(self, command_prefix, *args, **kwargs):
        super().__init__(command_prefix=command_prefix, *args, **kwargs)

    async def setup_hook(self):
        for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
            if filename.endswith(".py") and "__init__" not in filename:
                await bot.load_extension(name=f"cogs.{filename[:-3]}")
        return await super().setup_hook()


# async def load_extensions():
#     for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
#         if filename.endswith(".py") and "__init__" not in filename:
#             await bot.load_extension(name=f"cogs.{filename[:-3]}")

# @bot.event
# async def setup_hook():
#     for filename in os.listdir(path=path.join(configs.ROOT_DIR, "cogs")):
#         if filename.endswith(".py") and "__init__" not in filename:
#             await bot.load_extension(name=f"cogs.{filename[:-3]}")

# async def main():
#     async with bot:
#         await load_extensions()
#         # await bot.start(token=configs.TOKEN)
#     await bot.run(token=configs.TOKEN)

if __name__ == "__main__":
    bot = GatorTune(command_prefix=prefix, intents=Intents.all())
    bot.run(token=configs.TOKEN)

# @bot.command()
# async def ping(ctx: commands.Context):
#     await ctx.send(strings.PING)


# @bot.command(pass_context=True)  # change later to use cogs, then can use aliases
# async def play(ctx: commands.Context):
#     voice_client = utils.get(bot.voice_clients, guild=ctx.guild)

#     if voice_client:
#         await ctx.send(strings.ALRJOINED)
#         return

#     if ctx.author.voice:
#         channel = ctx.message.author.voice.channel
#         voice = await channel.connect()

#         # play audio
#         source = FFmpegPCMAudio("./audios/sunnyday.mp4")
#         player = voice.play(source=source)
#     else:
#         await ctx.send(strings.NOVOICE)

# @bot.command(pass_context=True)
# async def pause(ctx: commands.Context):
#     voice_client = utils.get(bot.voice_clients, guild=ctx.guild)
#     if voice_client.is_playing():
#         voice_client.pause


# @bot.command(pass_context=True)
# async def stop(ctx: commands.Context):
#     if ctx.voice_client:
#         await ctx.guild.voice_client.disconnect()
#         await ctx.send(strings.LEAVE)
#     else:
#         await ctx.send(strings.IDLE)


# @bot.command(pass_context=True)  # later
# async def repeat(ctx: commands.Context, type: Literal["on", "off", "all"]):
#     pass


# bot.run(token=configs.TOKEN)
