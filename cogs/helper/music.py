import re
import time
from functools import partial
from threading import Thread
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

    def _get_voice_ch(self, guild: Guild):
        return cast(VoiceClient, guild.voice_client)

    def send_message(self, ctx: Context, msg: str, wait=False) -> Message | None:
        """Exclusive use for non-async methods"""
        # wait here is to prevent _next for some reason locking the whole loop
        # if send message is being waited
        message = self.bot.loop.create_task(ctx.send(msg))
        if wait:
            while not message.done():
                time.sleep(1)
            return message.result()

    def edit_message(self, msg: Message, content: str, wait=False) -> Message | None:
        """Exclusive use for non-async methods"""
        message = self.bot.loop.create_task(msg.edit(content=content))
        if wait:
            while not message.done():
                time.sleep(1)
            return message.result()

    def playlist_parse_queue(
        self,
        s_queue: list[PlaylistQueue],
        queue: list[Queue],
        guild: Guild,
    ):
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

    def connect(self, ctx: Context) -> VoiceClient:
        assert isinstance(ctx.author, Member)
        assert isinstance(ctx.author.voice, VoiceState)
        assert isinstance(ctx.author.voice.channel, VoiceChannel)

        connect = self.bot.loop.create_task(ctx.author.voice.channel.connect())
        while not connect.done():
            time.sleep(1)

        return connect.result()

    def play(self, ctx: Context, query: Tuple[str, ...], cnt=0):
        """
        Recommended to be used with Threading to avoid blocking the main loop, allowing
        the play command to be immediately responsive for the next invocation
        """
        assert ctx.guild is not None
        assert isinstance(ctx.author, Member)
        assert isinstance(ctx.author.voice, VoiceState)
        assert isinstance(ctx.author.voice.channel, VoiceChannel)
        guild = ctx.guild

        curr_db = self.bot.database.get(guild.id)
        queue = curr_db["queue"]
        voice = self._get_voice_ch(guild)

        # sometimes the bot be disconnecting in the middle of playing so yeah
        if voice is None or not voice.is_connected():
            connect = self.connect(ctx)
            curr_db["voice_channel"] = connect.channel.id
        elif voice.channel.id != ctx.author.voice.channel.id:
            self.send_message(ctx, strings.Gator.EXISTS_VC)

        # check whether the join was successful or not
        voice = self._get_voice_ch(guild)
        if voice is None:
            return self.send_message(ctx, strings.Gator.LET_ME_IN)

        # check the failure count; cast to Message cause the wait is True
        if cnt == 0:
            status = self.send_message(ctx, strings.Gator.LOAD, True)
        else:
            status = self.send_message(ctx, strings.Gator.ERR_BOTDT[cnt], True)
        status = cast(Message, status)

        # the song
        song = " ".join(query)
        s_url = s_id = s_title = s_dur = ""
        s_queue: list[PlaylistQueue] | None = None
        playlist = re.findall(r"(?<=list=)[\w-]+", song)

        # update the db
        self.bot.database.update(guild, curr_db)

        # attempt to play the song
        try:
            if len(playlist) > 0:
                pl_id = playlist[0]
                s_id, s_title, s_dur, s_queue, pl_title = self.utils.playlist(id=pl_id)
                if cnt == 0:
                    self.send_message(
                        ctx, strings.Gator.IS_PLAYLS.format(len(s_queue), pl_title)
                    )
            else:
                s_url, s_id, s_title, s_dur = self.utils.search(song=song)
            source = s_url or self.utils.stream(video_id=s_id)
            new_queue: Queue = {
                "id": s_id,
                "title": s_title,
                "duration": s_dur,
                "source": source,
            }
            queue.append(new_queue)

            if s_queue is not None:
                bg_thread = Thread(
                    target=partial(
                        self.playlist_parse_queue,
                        s_queue=s_queue,
                        queue=queue,
                        guild=guild,
                    ),
                    daemon=True,
                )
                bg_thread.start()

            if voice.is_playing():
                self.edit_message(status, strings.Gator.ADD_QUEUE.format(s_title))
            else:
                # probably the most important bit is here lol
                voice.play(
                    self.utils.ffmpeg(song=source),
                    after=lambda _: self.next(ctx=ctx, guild=guild),
                )
                self.edit_message(status, strings.Gator.PLAY.format(s_title))
        except BotDetection:
            log_error(strings.Log.ERR_BOTDT)
            if cnt != 3:
                self.utils.token()
                self.play(ctx, query, cnt + 1)
            else:
                self.send_message(ctx, strings.Gator.ERR_GIVUP.format(OWNER))
        except RegexMatchError:
            log_error(format_exc())
            log_error(strings.Log.ERR_PYTUB)
            self.send_message(ctx, strings.Gator.ERR_PYTUB.format(OWNER))
        except KeyError as playlist_private:
            log_error(format_exc())
            log_error(strings.Log.ERR_PLYPV)
            if "header" in str(playlist_private):
                self.send_message(ctx, strings.Gator.ERR_PLYLS)
            else:
                self.send_message(ctx, strings.Gator.ERR_GENRL)
        except Exception:
            log_error(format_exc())
            self.send_message(ctx, strings.Gator.ERR_GENRL)

    def next(self, ctx: Context, guild: Guild):
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
            voice = self._get_voice_ch(guild)
            voice.play(
                self.utils.ffmpeg(song=source),
                after=lambda _: self.next(ctx=ctx, guild=guild),
            )
            self.send_message(ctx, strings.Gator.PLAY.format(title))
        else:
            self.send_message(ctx, strings.Gator.DONE)

    async def disconnect(self, guild: Guild):
        curr_db = self.bot.database.get(guild.id)
        text_id = curr_db["text_channel"]
        voice_ch = self._get_voice_ch(guild)
        queue = curr_db["queue"]

        queue.clear()

        if voice_ch.is_playing():
            voice_ch.stop()
        await voice_ch.disconnect()

        # clear the referenced voice channel
        curr_db["voice_channel"] = None

        if text_id:
            text_ch = cast(TextChannel, guild.get_channel(text_id))
            await text_ch.send(strings.Gator.LEAV)

        # update the db
        self.bot.database.update(guild, curr_db)
        log_info(strings.Log.MONTY_LVE.format(guild.name))
