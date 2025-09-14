import importlib
from typing import Literal, cast

from discord import Guild, Member, TextChannel, VoiceClient, VoiceState
from discord.ext import commands

import cogs.helper.music as helper
import utilities.classes.utilities as utilities
import utilities.strings as strings
from cogs.helper.music import MusicCogHelper
from configs import CONFIG
from main import GatorTune

# since typed variables is usually not a python thing, the linter
# panics since I tried using the Music class from classes.music,
# although technically it is valid since Music from classes.music
# is a child of types.music. 
from utilities.classes.types import Music
from utilities.classes.utilities import MusicUtils, log_info
from utilities.helper import check_author


class MusicCog(commands.Cog):
    def __init__(self, bot: GatorTune):
        self.bot = bot
        self.utils = MusicUtils()
        self.helper = MusicCogHelper(bot, self.utils)
        importlib.reload(helper)
        importlib.reload(strings)
        importlib.reload(utilities)

    def _get_text_ch(self, guild: Guild):
        curr_db = self.bot.database.get(guild.id)
        assert curr_db["text_channel"] is not None
        text_ch = guild.get_channel(curr_db["text_channel"])
        assert isinstance(text_ch, TextChannel)
        return text_ch

    async def _get_voice_ch(self, ctx: commands.Context):
        assert ctx.guild is not None
        await check_author(ctx)
        return cast(VoiceClient | None, ctx.guild.voice_client)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        """
        Remove the guild from the database when the bot is removed from a guild,
        since the bot can still join and play a music in a vc when it's removed
        """
        self.bot.database.remove(guild=guild)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, _: VoiceState
    ):
        """
        Will only be used to check the remaining members in a vc and whether
        or not the bot should disconnect
        """
        # thanks gemini lol. adjusted a bit from its recommendation
        if before.channel:
            members = before.channel.members
            all_bots = all(member.bot for member in members)
            if all_bots and (self.bot.user in members):
                guild = member.guild
                text_ch = self._get_text_ch(guild)
                leave_seconds = CONFIG["leave_seconds"]

                log_info(strings.Log.LAST_MMBR.format(guild.name, leave_seconds))

                await text_ch.send(strings.Gator.LONE)
                await self.helper.disconnect(guild)

    @commands.command(name="vc")
    async def vc(self, ctx: commands.Context):
        """
        There's a fucking bug in the built in library of discord
        where the return type of ctx.voice_client is VoiceProtocol
        instead of VoiceClient, confusing the hell out of me for
        a fucking day. Thank fucking you discord
        """
        assert isinstance(ctx.voice_client, VoiceClient)

    @commands.command(name="play", aliases=CONFIG["commands"]["play"])
    async def play(self, ctx: commands.Context, *query: str):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        assert isinstance(ctx.author, Member)
        log_info(strings.Log.PLY_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        curr_db = self.bot.database.get(guild.id)
        curr_db["text_channel"] = ctx.channel.id
        self.bot.database.update(guild=guild, data=curr_db)

        if not query:
            return await ctx.send(strings.Gator.NO_SQUERY)

        await self.helper.play(ctx, query)

    @commands.command(name="now_playing", aliases=CONFIG["commands"]["now_playing"])
    async def now_playing(self, ctx: commands.Context):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        curr_db = self.bot.database.get(ctx.guild.id)
        playing = curr_db["queue"][0]

        msg = strings.Gator.NOW_PLYNG.format(playing.title, playing.duration)
        await ctx.send(msg)

    @commands.command(name="remove", aliases=CONFIG["commands"]["remove"])
    async def remove(self, ctx: commands.Context, *index: str):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        guild = ctx.guild
        log_info(strings.Log.RME_INVKD.format(ctx.author, guild.name))

        curr_db = self.bot.database.get(guild.id)
        queue = curr_db["queue"]
        queue_len = len(queue)
        if not index:
            return await ctx.send(strings.Gator.INV_INTGR)
        elif queue_len < 1:
            return await ctx.send(strings.Gator.NO_SQUEUE)
        try:
            idx = int(" ".join(index)) - 1
            if idx < 0:
                raise ValueError
            removed: Music = queue.pop(idx)
            await ctx.send(strings.Gator.RMVD.format(removed.title))
        except ValueError:
            await ctx.send(strings.Gator.INV_INTGR)
        except IndexError:
            await ctx.send(strings.Gator.INV_REMOV.format(queue_len))

    @commands.command(name="pause", aliases=CONFIG["commands"]["pause"])
    async def pause(self, ctx: commands.Context):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        log_info(strings.Log.PSE_INVKD.format(ctx.author, ctx.guild.name))
        voice = await self._get_voice_ch(ctx)

        if voice is None:
            await ctx.send(strings.Gator.NO_PLAYNG)
        elif voice.is_playing():
            voice.pause()
            await ctx.send(strings.Gator.PAUS)
        else:
            await ctx.send(strings.Gator.NO_PLAYNG)

    @commands.command(name="resume", aliases=CONFIG["commands"]["resume"])
    async def resume(self, ctx: commands.Context):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        log_info(strings.Log.RSM_INVKD.format(ctx.author, ctx.guild.name))
        voice = await self._get_voice_ch(ctx)

        if voice is None:
            await ctx.send(strings.Gator.NO_PLAYNG)
        elif voice.is_paused():
            voice.resume()
            await ctx.send(strings.Gator.RSME)
        else:
            await ctx.send(strings.Gator.NO_PAUSED)

    @commands.command(name="repeat", aliases=CONFIG["commands"]["repeat"])
    async def repeat(self, ctx: commands.Context, *mode: str):
        """Mode should be `on, off,` or `all`. Literal isn't used to avoid BadLiteral error"""
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        log_info(strings.Log.RPT_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        curr_db = self.bot.database.get(guild.id)

        repeat: Literal["on", "off", "all"] = " ".join(mode)  # type: ignore -> pain

        if not repeat:
            repeat = "all"
            await ctx.send(strings.Gator.TIP_RPEAT.format(repeat))
        elif repeat.strip().lower() not in ["on", "off", "all"]:
            return await ctx.send(strings.Gator.INV_RPEAT.format(curr_db["repeat"]))
        else:
            await ctx.send(strings.Gator.LOOP.format(repeat))

        curr_db["repeat"] = repeat
        self.bot.database.update(guild, curr_db)

    @commands.command(name="skip", aliases=CONFIG["commands"]["skip"])
    async def skip(self, ctx: commands.Context):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        log_info(strings.Log.SKP_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        voice = await self._get_voice_ch(ctx)
        if voice is None:
            return await ctx.send(strings.Gator.NO_PLAYNG)

        if voice.is_playing():
            voice.pause()

        await ctx.send(strings.Gator.SKIP)
        log_info(strings.Log.S_SKIPPED.format(ctx.guild.name))

        await self.helper.next(ctx=ctx, guild=guild)

    @commands.command(name="stop", aliases=CONFIG["commands"]["stop"])
    async def stop(self, ctx: commands.Context):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        log_info(strings.Log.STP_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        voice = await self._get_voice_ch(ctx)

        curr_db = self.bot.database.get(guild.id)
        curr_db["queue"].clear()

        if voice is None:
            await ctx.send(strings.Gator.NO_PLAYNG)
        elif voice.is_playing():
            voice.stop()
            await ctx.send(strings.Gator.STOP)
        else:
            await ctx.send(strings.Gator.IDLE)

        self.bot.database.update(guild, curr_db)
        log_info(strings.Log.S_STOPPED.format(ctx.guild.name))

    @commands.command(name="clear", aliases=CONFIG["commands"]["clear"])
    async def clear(self, ctx: commands.Context):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        log_info(strings.Log.CLS_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        curr_db = self.bot.database.get(guild.id)
        queue = curr_db["queue"]

        log_info(strings.Log.CUR_QUEUE.format(queue))
        queue.clear()
        log_info(strings.Log.S_QUE_CLS.format(ctx.guild.name, queue))

        self.bot.database.update(guild, curr_db)
        await ctx.send(strings.Gator.CLS_QUEUE)

    @commands.command(name="leave", aliases=CONFIG["commands"]["leave"])
    async def leave(self, ctx: commands.Context):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        log_info(strings.Log.LVE_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        voice = await self._get_voice_ch(ctx)

        if self.helper.zombified(guild):
            voice = await self.helper.reconnect(guild)
        if voice is None:
            return await ctx.send(strings.Gator.NO_BVOICE)

        await self.helper.disconnect(guild, ctx)

    @commands.command(name="queue", aliases=CONFIG["commands"]["queue"])
    async def queue(self, ctx: commands.Context):
        if not await check_author(ctx):
            return False
        assert ctx.guild is not None
        log_info(strings.Log.QUE_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        curr_db = self.bot.database.get(guild.id)
        queue = curr_db["queue"]

        trimmed = ""
        for idx, song in enumerate(queue):
            trimmed += strings.Gator.LS_SQUEUE.format(
                idx + 1, song.title, song.duration
            )

        await ctx.send(trimmed or strings.Gator.NO_SQUEUE)


async def setup(bot: GatorTune):
    await bot.add_cog(MusicCog(bot=bot))
