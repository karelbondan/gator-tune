from discord import Member
from discord.ext.commands import Context

import utilities.strings as strings


async def check_author(ctx: Context):
    assert ctx.author is not None
    if not isinstance(ctx.author, Member):
        await ctx.send("Invoke this command from a server")
        return False
    assert isinstance(ctx.author, Member)
    if not ctx.author.voice:
        await ctx.send(strings.Gator.NO_UVOICE)
        return False
    return True
