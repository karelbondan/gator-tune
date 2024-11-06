from discord.ext import commands
from discord import Guild, VoiceClient, Member, Message, VoiceState
from utilities.utilities import log_info
from functools import partial
import re
import configs
import time
import threading
import utilities.namedtypes as namedtypes
import utilities.strings as strings
import utilities.utilities as utilities


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: namedtypes.Db = {}
        self.music_utils = utilities.Music()

    @commands.Cog.listener()
    async def on_ready(self):
        log_info(strings.Log.RDY_INVKD)
        for guild in self.bot.guilds:
            self._add_to_db(guild=guild)
        log_info(repr(self.db))

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        self._add_to_db(guild=guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        self._remove_from_db(guild=guild)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        guild = member.guild
        me = self._get_db(guild=guild)
        text_channel = me["text_channel"]

        # debug
        bfr = aft = []
        # if user joins before will be null
        try:
            members = bfr = before.channel.members
        # if user leaves after will be null
        # other changes like changing name, user mutes and unmutes will result in both being
        # not null, but that'll be discarded since we only want to check the last member
        except:
            members = aft = after.channel.members

        log_info(f"{guild.name}: [{len(bfr)}, {len(aft)}]")

        if len(members) == 1 and members[0].id == self.bot.user.id:
            leave_seconds = configs.CONFIG["leave_seconds"]
            log_info(strings.Log.LAST_MMBR.format(guild.name, leave_seconds))

            await text_channel.send(strings.Gator.LONE)
            await self._disconnect(guild=guild)

    @commands.command(name="play", aliases=configs.CONFIG["commands"]["play"])
    async def play(self, ctx: commands.Context, *query: str):
        log_info(strings.Log.PLY_INVKD.format(ctx.author, ctx.guild.name))

        # declarations
        guild = ctx.guild
        me = self._get_db(guild=guild)
        me["text_channel"] = ctx

        # fmt:off
        if not query:
            await ctx.send(strings.Gator.NO_SQUERY); return

        author_voice = ctx.author.voice
        if author_voice is None:
            await ctx.send(strings.Gator.NO_UVOICE); return
        # fmt:on

        play_thread = threading.Thread(
            target=partial(self._play, ctx=ctx, guild=guild, query=query, me=me),
            daemon=True,
        )
        play_thread.start()

    @commands.command(name="pause", aliases=configs.CONFIG["commands"]["pause"])
    async def pause(self, ctx: commands.Context):
        guild = ctx.guild
        voice: VoiceClient = self._get_voice_channel(guild=guild)

        if voice is None:
            await ctx.send(strings.Gator.NO_PLAYNG)
        elif voice.is_playing():
            voice.pause()
            await ctx.send(strings.Gator.PAUS)
        else:
            await ctx.send(strings.Gator.NO_PLAYNG)

    @commands.command(name="resume", aliases=configs.CONFIG["commands"]["resume"])
    async def resume(self, ctx: commands.Context):
        guild = ctx.guild
        voice: VoiceClient = self._get_voice_channel(guild=guild)

        if voice is None:
            await ctx.send(strings.Gator.NO_PLAYNG)
        elif voice.is_paused():
            voice.resume()
            await ctx.send(strings.Gator.RSME)
        else:
            await ctx.send(strings.Gator.NO_PAUSED)

    @commands.command(name="repeat", aliases=configs.CONFIG["commands"]["repeat"])
    # mode should be on, off, or all. Literal isn't used to avoid BadLiteral error
    async def repeat(self, ctx: commands.Context, *mode: str):
        # refs
        guild = ctx.guild
        me = self._get_db(guild=guild)

        mode: str = " ".join(mode)

        # fmt:off
        if not mode:
            mode = "all"
            await ctx.send(strings.Gator.TIP_RPEAT.format(mode))
        elif mode.strip().lower() not in ["on", "off", "all"]: 
            await ctx.send(strings.Gator.INV_RPEAT.format(me["repeat"])); return
        else:
            await ctx.send(strings.Gator.LOOP.format(mode))
        # fmt:on

        # save repeat mode to db
        me["repeat"] = mode

    @commands.command(name="skip", aliases=configs.CONFIG["commands"]["skip"])
    async def skip(self, ctx: commands.Context):
        log_info(strings.Log.SKP_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        voice: VoiceClient = self._get_voice_channel(guild=guild)
        # fmt:off
        if voice is None:
            await ctx.send(strings.Gator.NO_PLAYNG); return
        # fmt:on

        if voice.is_playing():
            voice.pause()

        await ctx.send(strings.Gator.SKIP)
        log_info(strings.Log.S_SKIPPED.format(ctx.guild.name))

        # skip
        self._next(ctx=ctx, guild=guild)

    @commands.command(name="stop", aliases=configs.CONFIG["commands"]["stop"])
    async def stop(self, ctx: commands.Context):
        log_info(strings.Log.STP_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        voice: VoiceClient = self._get_voice_channel(guild=guild)

        me = self._get_db(guild=guild)
        me["queue"].clear()

        if voice is None:
            await ctx.send(strings.Gator.NO_PLAYNG)
        elif voice.is_playing():
            voice.stop()
            await ctx.send(strings.Gator.STOP)
        else:
            await ctx.send(strings.Gator.IDLE)

        log_info(strings.Log.S_STOPPED.format(ctx.guild.name))

    @commands.command(name="clear", aliases=configs.CONFIG["commands"]["clear"])
    async def clear(self, ctx: commands.Context):
        log_info(strings.Log.CLS_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        me = self._get_db(guild=guild)
        queue = self._get_queue(me=me)

        log_info(strings.Log.CUR_QUEUE.format(queue))
        queue.clear()
        log_info(strings.Log.S_QUE_CLS.format(ctx.guild.name, queue))

        await ctx.send(strings.Gator.CLS_QUEUE)

    @commands.command(name="leave", aliases=configs.CONFIG["commands"]["leave"])
    async def leave(self, ctx: commands.Context):
        log_info(strings.Log.LVE_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        voice: VoiceClient = self._get_voice_channel(guild=guild)
        if voice is not None:
            await self._disconnect(guild=guild)
        else:
            await ctx.send(strings.Gator.NO_BVOICE)

    @commands.command(name="queue", aliases=configs.CONFIG["commands"]["queue"])
    async def queue(self, ctx: commands.Context):
        log_info(strings.Log.QUE_INVKD.format(ctx.author, ctx.guild.name))

        guild = ctx.guild
        me = self._get_db(guild=guild)
        queue = self._get_queue(me=me)

        trimmed = []
        for i in queue:
            trimmed.append({"title": i["title"]})

        await ctx.send(trimmed)

    def _add_to_db(self, guild: Guild):
        """Instantiates a new database record of a newly joined guild"""
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

    def _remove_from_db(self, guild: Guild):
        """Remove a guild's database"""
        if guild.id in self.db:
            self.db.pop(guild.id)

    def _get_voice_channel(self, guild: Guild) -> VoiceClient:
        """Get the guild's voice channel that GatorTune is currently connected to"""
        return self.db[guild.id]["voice_channel"]

    def _get_db(self, guild: Guild) -> namedtypes.State:
        """Get database for supplied guild"""
        return self.db[guild.id]

    def _get_queue(self, me: namedtypes.State) -> list[namedtypes.Queue]:
        """Get queue for supplied database of a guild"""
        return me["queue"]

    def _send_message(
        self, ctx: commands.Context, msg: str, wait=False
    ) -> Message | None:
        """Exclusive use for non-async methods"""
        # wait here is to prevent _next for some reason locking the whole loop
        # if send message is being waited
        message = self.bot.loop.create_task(ctx.send(msg))
        if wait:
            while not message.done():
                time.sleep(1)
            return message.result()
        # fmt:off
        else: return
        # fmt:on

    def _edit_message(self, msg: Message, content: str, wait=False) -> Message | None:
        """Exclusive use for non-async methods"""
        message = self.bot.loop.create_task(msg.edit(content=content))
        if wait:
            while not message.done():
                time.sleep(1)
            return message.result()
        # fmt:off
        else: return
        # fmt:on

    def _playlist_parse_queue(
        self,
        s_queue: list[namedtypes.PlaylistQueue],
        queue: list[namedtypes.Queue],
        guild: Guild,
    ):
        """Recommended to be used with Threading to avoid blocking the main event loop"""
        log_info("Thread to acquire playlist data started for {}".format(guild.name))
        for song in s_queue:
            source = self.music_utils.stream(video_id=song["id"])
            new_queue: namedtypes.Queue = {
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

    def _play(
        self, ctx: commands.Context, guild: Guild, query: str, me: namedtypes.State
    ):
        """
        Recommended to be used with Threading to avoid blocking the main loop, allowing
        the play command to be immediately responsive for the next invocation
        """
        author_voice = ctx.author.voice
        queue: list[namedtypes.Queue] = me["queue"]
        voice: VoiceClient = self._get_voice_channel(guild=guild)
        if voice is None:
            # connect to author's vc and reference it for later
            connect = self.bot.loop.create_task(author_voice.channel.connect())
            while not connect.done():
                time.sleep(1)
            me["voice_channel"] = connect.result()

        elif voice.channel.id != author_voice.channel.id:
            self._send_message(ctx, strings.Gator.EXISTS_VC)

        # fmt:off
        # check whether the join was successful or not
        voice: VoiceClient = self._get_voice_channel(guild=guild)
        if voice is None:
            self._send_message(ctx, strings.Gator.LET_ME_IN); return
        # fmt:on

        status: Message = self._send_message(ctx, strings.Gator.LOAD, True)

        # the song
        song = " ".join(query)
        s_id = s_title = s_dur = ""
        s_queue: list[namedtypes.PlaylistQueue] | None = None
        playlist = re.findall(r"(?<=list=)[\w-]+", song)
        try:
            if len(playlist) > 0:
                id = playlist[0]
                s_id, s_title, s_dur, s_queue = self.music_utils.playlist(id=id)
            else:
                s_id, s_title, s_dur = self.music_utils.search(song=song)
            source = self.music_utils.stream(video_id=s_id)
            new_queue: namedtypes.Queue = {
                "id": s_id,
                "title": s_title,
                "duration": s_dur,
                "source": source,
            }
            queue.append(new_queue)

            if s_queue is not None:
                bg_thread = threading.Thread(
                    target=partial(
                        self._playlist_parse_queue,
                        s_queue=s_queue,
                        queue=queue,
                        guild=guild,
                    ),
                    daemon=True,
                )
                bg_thread.start()

            if voice.is_playing():
                self._edit_message(status, strings.Gator.ADD_QUEUE.format(s_title))
            else:
                # probably the most important bit is here lol
                voice.play(
                    self.music_utils.ffmpeg(song=source),
                    after=lambda _: self._next(ctx=ctx, guild=guild),
                )
                self._edit_message(status, strings.Gator.PLAY.format(s_title))
        except Exception as e:
            utilities.log_error(repr(e))
            self._send_message(ctx, strings.Gator.ERR_GENRL)

    def _next(self, ctx: commands.Context, guild: Guild):
        """Exclusive use: only to play the next song in queue"""
        # references
        me = self._get_db(guild=guild)
        queue = self._get_queue(me=me)
        repeat_mode = me["repeat"]

        try:
            if repeat_mode == "all":
                queue.append(queue.pop(0))
            elif repeat_mode == "off":
                queue.pop(0)
        # fmt:off
        except: pass
        # fmt:on

        if len(queue) > 0:
            source = queue[0]["source"]
            title = queue[0]["title"]
            voice: VoiceClient = self._get_voice_channel(guild=guild)
            voice.play(
                self.music_utils.ffmpeg(song=source),
                after=lambda _: self._next(ctx=ctx, guild=guild),
            )
            self._send_message(ctx, strings.Gator.PLAY.format(title))
        else:
            self._send_message(ctx, strings.Gator.DONE)

    async def _disconnect(self, guild: Guild):
        me = self._get_db(guild=guild)
        text_channel = me["text_channel"]
        queue = me["queue"]
        voice: VoiceClient = self._get_voice_channel(guild=guild)

        queue.clear()

        if voice.is_playing():
            voice.stop()
        await voice.disconnect()

        # clear the referenced voice channel
        db = self._get_db(guild=guild)
        db["voice_channel"] = None

        await text_channel.send(strings.Gator.LEAV)
        log_info(strings.Log.MONTY_LVE.format(guild.name))


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot=bot))
