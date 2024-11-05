from discord.ext import commands
from discord import Guild, VoiceClient, Message, Member, VoiceState
from typing import Literal
from os import path
from utilities.utilities import log_info, log_error
from asyncio import run_coroutine_threadsafe, create_task
import utilities.namedtypes as namedtypes
import configs
import utilities.strings as strings
import utilities.utilities as utilities


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: namedtypes.Db = {}
        self.music_utils = utilities.Music()

    def setup(self):
        pass

    def add_to_db(self, guild: Guild):
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

    def remove_from_db(self, guild: Guild):
        if guild.id in self.db:
            self.db.pop(guild.id)

    def get_voice_channel(self, guild: Guild) -> VoiceClient:
        return self.db[guild.id]["voice_channel"]

    def get_db(self, guild: Guild) -> namedtypes.State:
        return self.db[guild.id]

    def _get_queue(self, me: namedtypes.State) -> list[namedtypes.Queue]:
        return me["queue"]

    @commands.Cog.listener()
    async def on_ready(self):
        log_info("OnReady invoked from Music cog")
        for guild in self.bot.guilds:
            self.add_to_db(guild=guild)
        log_info(repr(self.db))

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        self.add_to_db(guild=guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        self.remove_from_db(guild=guild)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: Member,
        before: VoiceState,
        after: VoiceState,
    ):
        guild = member.guild
        me = self.get_db(guild=guild)
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
            log_info(
                "Bot is the last member in {}, leaving in {} seconds".format(
                    guild.name, configs.CONFIG["leave_seconds"]
                )
            )
            await text_channel.send(
                "No one's here anymore? Good, Imma head back to my room"
            )
            await self._disconnect(guild=guild)

    @commands.command(name="play", aliases=configs.CONFIG["commands"]["play"])
    async def play(self, ctx: commands.Context, *query: str):
        log_info(f"Play command invoked by {ctx.author} from {ctx.guild.name}")

        # declarations
        guild = ctx.guild
        # me = self.db[guild.id]
        me = self.get_db(guild=guild)
        me["text_channel"] = ctx
        queue: list[namedtypes.Queue] = me["queue"]

        # fmt:off
        if not query:
            await ctx.send(strings.NOQUERY); return

        author_voice = ctx.author.voice
        if author_voice is None:
            await ctx.send(strings.NOVOICE); return
        # fmt:on

        voice: VoiceClient = self.get_voice_channel(guild=guild)
        if voice is None:
            # connect to author's vc and reference it for later
            me["voice_channel"] = await author_voice.channel.connect()
        elif voice.channel.id != author_voice.channel.id:
            await ctx.send(strings.ALRJOINED)

        # fmt:off
        # check whether the join was successful or not
        voice: VoiceClient = self.get_voice_channel(guild=guild)
        if voice is None:
            await ctx.send(strings.LETMEIN); return
        # fmt:on

        status_msg = await ctx.send(strings.LOADING)

        # the song
        song = " ".join(query)
        song_id = song_title = ""
        try:
            song_id, song_title = self.music_utils.search(song=song)
            source = self.music_utils.stream(video_id=song_id)
            queue.append({"id": song_id, "title": song_title, "source": source})

            if voice.is_playing():
                await status_msg.edit(
                    content="🎸 Got it, I've add **{}** to the queue".format(song_title)
                )
            else:
                # probably the most important bit is here lol
                voice.play(
                    self.music_utils.ffmpeg(song=source),
                    after=lambda _: self._next(ctx=ctx, guild=guild),
                )
                await status_msg.edit(
                    content="🎸 Now rocking **{}**".format(song_title)
                )
        except Exception as e:
            utilities.log_error(repr(e))
            await ctx.send(strings.PLAYERROR)

    @commands.command(name="pause", aliases=configs.CONFIG["commands"]["pause"])
    async def pause(self, ctx: commands.Context):
        guild = ctx.guild
        voice: VoiceClient = self.get_voice_channel(guild=guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send("Paused")
        else:
            await ctx.send("No song is playing")

    @commands.command(name="resume", aliases=configs.CONFIG["commands"]["resume"])
    async def resume(self, ctx: commands.Context):
        guild = ctx.guild
        voice: VoiceClient = self.get_voice_channel(guild=guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send("Resumed")
        else:
            await ctx.send("No song is paused")

    @commands.command(name="repeat", aliases=configs.CONFIG["commands"]["repeat"])
    async def repeat(
        self,
        ctx: commands.Context,
        mode: Literal["on", "off", "all"] = "all",
    ):
        guild = ctx.guild
        # db; set queue mode
        db = self.get_db(guild=guild)
        db["repeat"] = mode
        # send info
        await ctx.send("Repeat mode is now set to {}".format(mode))

    @commands.command(name="skip", aliases=configs.CONFIG["commands"]["skip"])
    async def skip(self, ctx: commands.Context):
        log_info(f"Skip command invoked by {ctx.author} from {ctx.guild.name}")

        guild = ctx.guild
        voice: VoiceClient = self.get_voice_channel(guild=guild)
        if voice.is_playing():
            voice.pause()
        # skip
        self._next(ctx=ctx, guild=guild)

        await ctx.send("Skipped current song")
        log_info(f"A song playing in {ctx.guild.name} was skipped")

    @commands.command(name="stop", aliases=configs.CONFIG["commands"]["stop"])
    async def stop(self, ctx: commands.Context):
        log_info(f"Stop command invoked by {ctx.author} from {ctx.guild.name}")

        guild = ctx.guild
        voice: VoiceClient = self.get_voice_channel(guild=guild)
        voice.stop()

        await ctx.send("Rude, but I like your style")
        log_info(f"A song playing in {ctx.guild.name} was stopped")

    @commands.command(name="clear", aliases=configs.CONFIG["commands"]["clear"])
    async def clear(self, ctx: commands.Context):
        log_info(f"Clear queue command invoked by {ctx.author} from {ctx.guild.name}")

        guild = ctx.guild
        me = self.get_db(guild=guild)
        queue = self._get_queue(me=me)

        log_info(f"Current queue: {queue}")
        queue.clear()
        log_info(f"Song queue for {ctx.guild.name} has been cleared: {queue}")

        await ctx.send("Queue cleared")

    @commands.command(name="leave", aliases=configs.CONFIG["commands"]["leave"])
    async def leave(self, ctx: commands.Context):
        log_info(f"Leave command invoked by {ctx.author} from {ctx.guild.name}")

        guild = ctx.guild
        voice: VoiceClient = self.get_voice_channel(guild=guild)
        if voice is not None:
            await self._disconnect(guild=guild)
        else:
            await ctx.send("Not in a voice channel")

    @commands.command(name="queue", aliases=configs.CONFIG["commands"]["queue"])
    async def queue(self, ctx: commands.Context):
        log_info(f"List queue command invoked by {ctx.author} from {ctx.guild.name}")

        guild = ctx.guild
        me = self.get_db(guild=guild)
        queue = self._get_queue(me=me)

        trimmed = []
        for i in queue:
            trimmed.append({"title": i["title"]})

        await ctx.send(trimmed)

    def _next(self, ctx: commands.Context, guild: Guild):
        # references
        me = self.get_db(guild=guild)
        queue = self._get_queue(me=me)
        repeat_mode = me["repeat"]

        if len(queue) > 0:
            # edit the queue based on the repeat mode
            if repeat_mode == "all":
                queue.append(queue.pop(0))
            elif repeat_mode == "off":
                queue.pop(0)

            source = queue[0]["source"]
            voice: VoiceClient = self.get_voice_channel(guild=guild)
            voice.play(
                self.music_utils.ffmpeg(song=source),
                after=lambda _: self._next(ctx=ctx, guild=guild),
            )
            self._send_message(ctx, strings.NOWROCKING.format(queue[0]["title"]))
        else:
            self._send_message(ctx, strings.FINISHED)

    def _send_message(self, ctx: commands.Context, msg: str):
        msg = ctx.send(msg)

        # send msg info
        future = run_coroutine_threadsafe(msg, self.bot.loop)
        try:
            log_info(repr(future.result()))
        # fmt:off
        except: pass
        # fmt:on

    async def _disconnect(self, guild: Guild):
        me = self.get_db(guild=guild)
        text_channel = me["text_channel"]
        queue = me["queue"]
        voice: VoiceClient = self.get_voice_channel(guild=guild)

        # clear queue
        queue.clear()

        # stop if currently playing
        if voice.is_playing():
            voice.stop()

        # disconnect
        await voice.disconnect()

        # clear the referenced voice channel
        db = self.get_db(guild=guild)
        db["voice_channel"] = None

        await text_channel.send(strings.LEAVE)
        log_info(f"Monty has left {guild.name}")

    def _disconnect_after_seconds(self, guild: Guild):
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot=bot))
