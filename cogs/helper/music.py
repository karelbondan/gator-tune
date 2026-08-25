from __future__ import annotations

import asyncio
import re
from asyncio import run_coroutine_threadsafe
from traceback import format_exc
from typing import TYPE_CHECKING, Literal, cast

from discord import (
    Guild,
    Member,
    Message,
    TextChannel,
    VoiceChannel,
    VoiceClient,
    VoiceState,
    errors,
)
from discord.ext.commands import Context
from emoji import replace_emoji
from pytubefix.exceptions import BotDetection, RegexMatchError

from classes.audio import Audio
from classes.exceptions import (
    MisconfiguredService,
    NotImplementedYet,
    ServiceError,
    TokenGenerationFailure,
)
from classes.music_service import MusicService
from classes.music_utils import MusicUtils
from classes.selection import Selection
from classes.types import PlaylistQueue
from configs import OWNER, USE_SERVICE, YT
from model.music import Music
from utilities import strings
from utilities.log_helper import log_error, log_info
from configs import CONFIG

if TYPE_CHECKING:
    from main import GatorTune


class MusicCogHelper:
    def __init__(self, bot: GatorTune, utils: MusicUtils, svc: MusicService) -> None:
        self.bot = bot
        self.utils = utils
        self.service = svc

    def _after(self, err: Exception | None, ctx: Context, guild: Guild, src: Audio):
        exc = ""

        if err:
            exc = f"{strings.Gator.CNLG}: {err.__class__.__name__}: {err!s}"
        elif src.error_message:
            excs = re.findall(r".+(in#0|tcp).+\n", src.error_message, re.IGNORECASE)
            # keep the error if its length splitted by &, /, and \s,
            # 2 is under 40
            for e in excs:
                l = len(re.split(r"[&/\s]", e))
                e = cast(str, e).replace("\n", "")
                # -# is small text followed by code ``
                exc += f"-# `{strings.Gator.CNLG}: {e}`\n" if l < 40 else ""

        if exc:
            msg = f"{strings.Gator.ERR_STREAM}\n{exc}"
            run_coroutine_threadsafe(self.send_message(ctx, msg), self.bot.loop)

        run_coroutine_threadsafe(self.next(ctx, guild), self.bot.loop)

    def _queue(self, src: str, s: PlaylistQueue, q: list[Music], g: Guild):
        music = Music(
            bot=self.bot,
            id=s["id"],
            title=s["title"],
            creator="Placeholder",
            duration=s["duration"],
            lyrics="Placeholder",
            source=src,
            url=YT + s["id"],
        )
        q.append(music)
        log_info(
            "{} [{}] added to {}'s queue".format(s["title"], s["duration"], g.name)
        )

    async def _choose_format_message(self, selection: Selection):
        """For use by 'choose music' methods"""
        trimmed = selection.get_paginated()
        content = f"{strings.Gator.CHOOSE_ONE}\n"

        for idx, song in enumerate(trimmed):
            # [text](url) is like <a/> tag, <url> suppresses embed
            # the extra spacebreak on each appendage is intentional
            title = replace_emoji(song["title"], replace="")
            title = re.sub(r"[*_~`<>]", "", title)
            content += f"{idx + 1}. "
            content += f"[{title}](<{strings.Helper.YT_URL}{song['id']}>) "
            content += f"({song['duration']})\n"
        content += f"Page {selection.page} / {selection.total_page}"

        return content

    def zombified(self, guild: Guild):
        return guild.me.voice is not None and guild.voice_client is None

    def get_voice_ch(self, guild: Guild):
        return cast(VoiceClient | None, guild.voice_client)

    async def send_message(self, ctx: Context, msg: str):
        """Exclusive use for this helper class, supposedly"""
        return await ctx.send(msg)

    async def send_error(self, ctx: Context, msg: str, error: Exception):
        """For sending errors only"""
        # -# is small text followed by code ``
        detail = f"-# `{strings.Gator.CNLG}: {error.__class__.__name__}: {error!s}`"
        return await ctx.send(f"{msg}\n{detail}")

    async def edit_message(self, msg: Message, content: str):
        """Exclusive use for this helper class, supposedly"""
        return await msg.edit(content=content)

    async def connect(self, ctx: Context):
        assert isinstance(ctx.author, Member)
        assert isinstance(ctx.author.voice, VoiceState)
        assert isinstance(ctx.author.voice.channel, VoiceChannel)
        return await ctx.author.voice.channel.connect()

    async def reconnect(self, guild: Guild):
        assert guild.me.voice is not None
        assert isinstance(guild.me.voice.channel, VoiceChannel)
        return await guild.me.voice.channel.connect()

    async def disconnect(self, guild: Guild, ctx: Context | None = None):
        curr_db = self.bot.database.get(guild.id)
        text_id = curr_db["text_channel"]
        voice_ch = self.get_voice_ch(guild)
        queue = curr_db["queue"]

        queue.clear()

        print(self.zombified(guild))

        if self.zombified(guild):
            voice_ch = await self.reconnect(guild)
        assert voice_ch is not None

        if voice_ch.is_playing():
            voice_ch.stop()
        await voice_ch.disconnect()

        if text_id or ctx:
            text_ch = ctx or cast(TextChannel, guild.get_channel(text_id))  # type: ignore -> pain
            await text_ch.send(strings.Gator.LEAV)

        self.bot.database.remove(guild)
        log_info(strings.Log.MONTY_LVE.format(guild.name))

    async def playlist(
        self, s_queue: list[PlaylistQueue], queue: list[Music], guild: Guild
    ):
        """Recommended to be used with Threading to avoid blocking the main event loop"""
        log_info(f"Thread to acquire playlist data started for {guild.name}")

        loop = self.bot.loop
        for song in s_queue:
            if USE_SERVICE:
                src = await self.service.stream(song["id"])
            else:
                src = await loop.run_in_executor(None, self.utils.stream, song["id"])
            await loop.run_in_executor(None, self._queue, src, song, queue, guild)
            await asyncio.sleep(1)

        log_info(f"Acquire playlist data finished for {guild.name}")

    async def choose_change_page(self, guild_id: int, action: Literal["next", "prev"]):
        curr_db = self.bot.database.get(guild_id)
        selection = curr_db["active_selection"]

        if not selection or not selection.message:
            return False

        # call either .next() or .prev() based on the action
        # if it fails return early
        if not getattr(selection, action, lambda: None)():
            return False

        # cancel the timeout and create a new one
        selection.clear_timeout()

        # edit message
        content = await self._choose_format_message(selection)
        await selection.message.edit(content=content)

        # create a new timeout task
        loop = self.bot.loop
        task = loop.create_task(self.utils.create_timeout(selection, guild_id))
        selection.timeout_task = task

        return True

    async def chosen(self, guild_id: int, index: int):
        curr_db = self.bot.database.get(guild_id)
        selection = curr_db["active_selection"]

        if not selection or not selection.message:
            return False

        trimmed = selection.get_paginated()

        # this abomination is being done here because on the last page
        # the index could be higher than the length of the list hence the max
        # and vice versa with the min. the idea here is to prevent out of range
        # error on the last page. e.g. user reacted 5 but list only 3 in length.
        # using below with result in 3 % 5, which will result in 3, then minus 1
        # because array slicing moment
        index = (min(index, len(trimmed)) % max(index, len(trimmed))) - 1
        song = trimmed[index]

        ctx = selection.context
        try:
            # delete msg cache
            del curr_db["message_cache"][selection.message.id]

            # cancel asyncio timeout
            selection.clear_timeout()

            # delete the actual message and play the song
            await selection.message.delete()
            await self.play(ctx, (f"{strings.Helper.YT_URL}{song['id']}",))

            # reset the active selection for the current guild
            curr_db["active_selection"] = None
            return True

        except Exception as exc:  # noqa
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_ERROR, exc)
            return False

    async def choose(self, ctx: Context, query: tuple[str, ...]):
        try:
            if not USE_SERVICE:
                raise NotImplementedYet("Not implemented yet")

            assert isinstance(ctx.author, Member)
            assert isinstance(ctx.author.voice, VoiceState)
            assert isinstance(ctx.author.voice.channel, VoiceChannel)
            assert ctx.guild

            guild = ctx.guild
            curr_db = self.bot.database.get(guild.id)

            msg = await ctx.send(strings.Gator.CHOOSE_INIT)

            # get the song list
            songs = await self.service.choose(" ".join(query))

            # initialize the selection session and get the
            # paginated list
            timeout = CONFIG["choose_timeout"]
            selection = Selection(songs=songs, context=ctx, expire_seconds=timeout)

            # send message
            content = await self._choose_format_message(selection)
            await msg.edit(content=content)

            # add reactions for control
            numbers = selection.get_number_emojis()
            control = ["◀️", *numbers, "▶️"]
            tasks = [msg.add_reaction(emoji) for emoji in control]
            await asyncio.gather(*tasks)

            # update the message reference in the selection object
            selection.message = msg

            # create expiration task
            loop = self.bot.loop
            task = loop.create_task(self.utils.create_timeout(selection, guild.id))
            selection.timeout_task = task

            curr_db["active_selection"] = selection
            curr_db["message_cache"][msg.id] = msg
            self.bot.database.update(guild, curr_db)
        except MisconfiguredService as svc:
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_SERVICE, svc)
        except ServiceError as svc:
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_SERVICE, svc)
        except NotImplementedYet as not_impl:
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_NOT_IMPL, not_impl)
        except Exception as exc:  # noqa
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_ERROR, exc)

    async def play(self, ctx: Context, query: tuple[str, ...], cnt=0):
        assert isinstance(ctx.author, Member)
        assert isinstance(ctx.author.voice, VoiceState)
        assert isinstance(ctx.author.voice.channel, VoiceChannel)
        assert ctx.guild is not None
        guild = ctx.guild

        curr_db = self.bot.database.get(guild.id)
        queue = curr_db["queue"]
        voice = self.get_voice_ch(guild)

        # sometimes the bot be disconnecting in the middle of playing so yeah
        if voice is None or not voice.is_connected():
            if self.zombified(guild):
                connect = await self.reconnect(guild)
            else:
                connect = await self.connect(ctx)
            curr_db["voice_channel"] = connect.channel.id
        elif voice.channel.id != ctx.author.voice.channel.id:
            await self.send_message(ctx, strings.Gator.EXISTS_VC)

        # check whether the join was successful or not
        voice = self.get_voice_ch(guild)
        if voice is None:
            return await self.send_message(ctx, strings.Gator.LET_ME_IN)

        # check the failure count
        if cnt == 0:
            status = await self.send_message(ctx, strings.Gator.LOAD)
        else:
            status = await self.send_message(ctx, strings.Gator.ERR_BOTDT[cnt])

        # the song
        song = " ".join(query)
        possible_playlist = re.findall(r"(?<=list=)[\w-]+", song)

        # update the db
        self.bot.database.update(guild, curr_db)

        # get the bot's loop to let sync functions run in thread
        loop = self.bot.loop

        # attempt to play the song
        try:
            if possible_playlist:
                pl_id = possible_playlist[0]
                result = await loop.run_in_executor(None, self.utils.playlist, pl_id)
                if cnt == 0:
                    count = cast(list[PlaylistQueue], result["queue"])
                    title = cast(str, result["playlist_title"])
                    mesge = strings.Gator.IS_PLAYLS.format(len(count), title)
                    await self.send_message(ctx, mesge)
            elif USE_SERVICE:
                result = await loop.run_in_executor(None, self.service.search, song)
            else:
                result = await loop.run_in_executor(None, self.utils.search, song)

            if USE_SERVICE:
                source = result["url"] or await self.service.stream(result["id"])
            else:
                source = result["url"] or await loop.run_in_executor(
                    None, self.utils.stream, result["id"]
                )

            music = Music(
                bot=self.bot,
                id=result["id"],
                title=result["title"],
                creator="Placeholder",
                duration=result["duration"],
                lyrics="Placeholder",
                source=source,
                url=YT + result["id"],
            )
            queue.append(music)  # append queue

            if result["queue"] is not None:
                # thanks gemini
                # note to self -> asyncio.run_in_executor makes a new thread to run
                # the cpu bound process, while asyncio.create_task runs the async
                # process without the need to use await
                loop.create_task(self.playlist(result["queue"], queue, guild))

            if voice.is_playing():
                msg = strings.Gator.ADD_QUEUE.format(result["title"])
                await self.edit_message(status, msg)
            else:
                # probably the most important bit is here lol
                ffmpeg = self.utils.ffmpeg(song=source)
                voice.play(
                    ffmpeg, after=lambda e, f=ffmpeg: self._after(e, ctx, guild, f)
                )

                # edit message to show the newly played song
                msg = strings.Gator.PLAY.format(result["title"])
                await self.edit_message(status, msg)
        except BotDetection:
            log_error(strings.Log.ERR_BOTDT)
            try:
                if cnt != 3:
                    await self.utils.token()
                    await self.play(ctx, query, cnt + 1)
                else:
                    await self.send_message(ctx, strings.Gator.ERR_GIVUP.format(OWNER))
            except TokenGenerationFailure as e:
                await self.send_error(ctx, strings.Gator.ERR_INTERNAL.format(OWNER), e)
        except RegexMatchError as e:
            log_error(format_exc())
            log_error(strings.Log.ERR_PYTUB)
            await self.send_error(ctx, strings.Gator.ERR_PYTUB.format(OWNER), e)
        except KeyError as undefined:
            log_error(format_exc())
            if "header" in str(undefined):
                log_error(strings.Log.ERR_PLYPV)
                await self.send_message(ctx, strings.Gator.ERR_PLYLS)
            elif "visitorData" in str(undefined):
                log_error(strings.Log.ERR_INTERNAL.format(str(undefined)))
                await self.send_error(
                    ctx, strings.Gator.ERR_INTERNAL.format(OWNER), undefined
                )
            else:
                log_error(str(undefined))
                await self.send_error(ctx, strings.Gator.ERR_GENRL, undefined)
        except errors.ClientException as client:
            log_error(str(client))
            await self.send_error(ctx, strings.Gator.ERR_INTERNAL.format(OWNER), client)
        except MisconfiguredService as svc:
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_SERVICE, svc)
        except ServiceError as svc:
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_SERVICE, svc)
        except Exception as exc:  # noqa
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_ERROR, exc)

    async def next(self, ctx: Context, guild: Guild):
        """Exclusive use: only to play the next song in queue"""
        curr_db = self.bot.database.get(guild.id)
        queue = curr_db["queue"]
        repeat_mode = curr_db["repeat"]

        try:
            if repeat_mode == "all":
                queue.append(queue.pop(0))
            elif repeat_mode == "off":
                queue.pop(0)
        except Exception:  # noqa
            pass

        try:
            if len(queue) > 0:
                music = queue[0]
                expired = await music.expired()
                message = None
                if expired:
                    log_info(f"{guild.id}: URL expired, refetching...")
                    message = await self.send_message(ctx, strings.Gator.DOREFETCH)
                    await music.refetch(check=False)

                voice = self.get_voice_ch(guild)
                if self.zombified(guild):
                    voice = await self.reconnect(guild)
                assert voice is not None

                ffmpeg = self.utils.ffmpeg(song=music.source)
                voice.play(
                    ffmpeg, after=lambda e, f=ffmpeg: self._after(e, ctx, guild, f)
                )

                content = strings.Gator.PLAY.format(music.title)
                if message:
                    await message.edit(content=content)
                else:
                    await self.send_message(ctx, content)
            else:
                await self.send_message(ctx, strings.Gator.DONE)
        except MisconfiguredService as svc:
            # misconfigured external service --> v1 (deprecated)
            log_error(format_exc())
            await self.send_error(ctx, strings.Gator.ERR_SERVICE, svc)
