import re
from asyncio import run_coroutine_threadsafe
from traceback import format_exc
from typing import Tuple, cast

from discord import (
    Guild,
    Member,
    Message,
    TextChannel,
    VoiceChannel,
    VoiceClient,
    VoiceState,
)
from discord.ext.commands import Context
from pytubefix.exceptions import BotDetection, RegexMatchError

import utilities.strings as strings
from configs import OWNER
from main import GatorTune
from utilities.classes.types import PlaylistQueue, Queue
from utilities.classes.utilities import MusicUtils, log_error, log_info


class MusicCogHelper:
    def __init__(self, bot: GatorTune, utils: MusicUtils) -> None:
        self.bot = bot
        self.utils = utils

    # thanks chatgpt
    def _after(self, ctx: Context, guild: Guild):
        def callback(error: Exception | None):
            if error:
                pass
            else:
                run_coroutine_threadsafe(self.next(ctx, guild), self.bot.loop)

        return callback

    def zombified(self, guild: Guild):
        return guild.me.voice is not None and guild.voice_client is None

    def get_voice_ch(self, guild: Guild):
        return cast(VoiceClient | None, guild.voice_client)

    async def send_message(self, ctx: Context, msg: str):
        """Exclusive use for this helper class, supposedly"""
        return await ctx.send(msg)

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

    def playlist(self, s_queue: list[PlaylistQueue], queue: list[Queue], guild: Guild):
        """Recommended to be used with Threading to avoid blocking the main event loop"""
        log_info("Thread to acquire playlist data started for {}".format(guild.name))
        for song in s_queue:
            source = self.utils.stream(video_id=song["id"])
            new_queue: Queue = {
                "id": song["id"],
                "title": song["title"],
                "duration": song["duration"],
                "source": source,
            }
            queue.append(new_queue)
            log_info(
                "{} [{}] added to {}'s queue".format(
                    song["title"], song["duration"], guild.name
                )
            )
        log_info("Acquire playlist data finished for {}".format(guild.name))

    async def play(self, ctx: Context, query: Tuple[str, ...], cnt=0):
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
            else:
                result = await loop.run_in_executor(None, self.utils.search, song)
            source = result["url"] or self.utils.stream(video_id=result["id"])
            new_queue: Queue = {
                "id": result["id"],
                "title": result["title"],
                "duration": result["duration"],
                "source": source,
            }
            queue.append(new_queue)

            if result["queue"] is not None:
                # thanks gemini
                loop.run_in_executor(None, self.playlist, result["queue"], queue, guild)

            if voice.is_playing():
                msg = strings.Gator.ADD_QUEUE.format(result["title"])
                await self.edit_message(status, msg)
            else:
                # probably the most important bit is here lol
                ffmpeg = self.utils.ffmpeg(song=source)
                voice.play(ffmpeg, after=self._after(ctx, guild))

                # edit message to show the newly played song
                msg = strings.Gator.PLAY.format(result["title"])
                await self.edit_message(status, msg)
        except BotDetection:
            log_error(strings.Log.ERR_BOTDT)
            if cnt != 3:
                self.utils.token()
                await self.play(ctx, query, cnt + 1)
            else:
                await self.send_message(ctx, strings.Gator.ERR_GIVUP.format(OWNER))
        except RegexMatchError:
            log_error(format_exc())
            log_error(strings.Log.ERR_PYTUB)
            await self.send_message(ctx, strings.Gator.ERR_PYTUB.format(OWNER))
        except KeyError as playlist_private:
            log_error(format_exc())
            log_error(strings.Log.ERR_PLYPV)
            if "header" in str(playlist_private):
                await self.send_message(ctx, strings.Gator.ERR_PLYLS)
            else:
                await self.send_message(ctx, strings.Gator.ERR_GENRL)
        except Exception:
            log_error(format_exc())
            await self.send_message(ctx, strings.Gator.ERR_GENRL)

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
        except Exception:
            pass

        if len(queue) > 0:
            source = queue[0]["source"]
            title = queue[0]["title"]

            voice = self.get_voice_ch(guild)
            if self.zombified(guild):
                voice = await self.reconnect(guild)
            assert voice is not None

            ffmpeg = self.utils.ffmpeg(song=source)
            voice.play(ffmpeg, after=self._after(ctx, guild))

            await self.send_message(ctx, strings.Gator.PLAY.format(title))
        else:
            await self.send_message(ctx, strings.Gator.DONE)
