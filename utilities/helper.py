from discord import Member
from discord.ext.commands import Context
from pytubefix import YouTube

import utilities.strings as strings
from configs import YT


async def check_author(ctx: Context):
    """Check whether the author has invoked the command correctly"""
    assert ctx.author is not None
    if not isinstance(ctx.author, Member):
        await ctx.send("Invoke this command from a server")
        return False
    assert isinstance(ctx.author, Member)
    if not ctx.author.voice:
        await ctx.send(strings.Gator.NO_UVOICE)
        return False
    return True


def init():
    """This method is mainly used to trigger the oauth prompt"""
    yt = YouTube(url=YT + "dQw4w9WgXcQ", use_oauth=True)
    audio = yt.streams.get_audio_only()
    assert audio
    return audio.url
