from discord.ext import commands
from discord import Guild, VoiceClient, Message
from typing import Literal
from os import path
from utilities.utilities import log_info, log_error
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
                "voice_channel": None,
            }

    def remove_from_db(self, guild: Guild):
        if guild.id in self.db:
            self.db.pop(guild.id)

    def get_voice_channel(self, guild: Guild) -> VoiceClient:
        return self.db[guild.id]["voice_channel"]

    def get_db(self, guild: Guild) -> namedtypes.State:
        return self.db[guild.id]

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

    @commands.command(name="play", aliases=configs.CONFIG["commands"]["play"])
    async def play(self, ctx: commands.Context, *query: str):
        log_info(f"Play command invoked by {ctx.author} from {ctx.guild.name}")

        # declarations
        guild = ctx.guild
        me = self.db[guild.id]
        queue: list[str] = me["queue"]

        # fmt:off
        if not query:
            await ctx.send(strings.NOQUERY); return

        author_voice = ctx.author.voice
        if author_voice is None:
            await ctx.send(strings.NOVOICE); return
        # fmt:on

        voice: VoiceClient = self.get_voice_channel(guild=guild)
        # if voice is not None and voice.channel.id != author_voice.channel.id:
        #     await ctx.send(strings.ALRJOINED)
        # else:
        #     me["voice_channel"] = await author_voice.channel.connect()

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
            song = song_id + ".mp3"
            queue.append(song)
            source = path.join(configs.ROOT_DIR, "audios", song)
            
            if not path.exists(source):
                self.music_utils.download(song_id)
            
            voice.play(self.music_utils.ffmpeg(song=source))
            await status_msg.edit(content="**Now playing**: {}".format(song_title))
            # await voice.play(
            #     self.music_utils.ffmpeg("./audios/sunnyday.mp3"),
            #     after=lambda _: self.next(ctx=ctx, guild=guild),
            # )
        # except TypeError:
        #     self.music_utils.download(song_id)
        #     source = path.join(configs.ROOT_DIR, "audios", song_id)
        #     voice.play(self.music_utils.ffmpeg(song=source))
        #     await status_msg.edit(content="**Now playing**: {}".format(song_title))
        except Exception as e:
            utilities.log_error(repr(e))
            await ctx.send(strings.PLAYERROR)

    @commands.command(name="stop", aliases=configs.CONFIG["commands"]["stop"])
    async def stop(self, ctx: commands.Context):
        # guild
        guild = ctx.guild

        # get current voice client and stop playback
        voice: VoiceClient = self.get_voice_channel(guild=guild)
        voice.stop()

        await ctx.send("Stopped whatever you're playing before")

    @commands.command(name="leave", aliases=configs.CONFIG["commands"]["leave"])
    async def leave(self, ctx: commands.Context):
        # guild
        guild = ctx.guild

        # disconnect from current voice channel
        voice: VoiceClient = self.get_voice_channel(guild=guild)
        await voice.disconnect()

        # clear the referenced voice channel
        db = self.get_db(guild=guild)
        db["voice_channel"] = None

        await ctx.send(strings.LEAVE)

    def next(
        self,
        ctx: commands.Context,
        guild: Guild,
        mode: Literal["on", "off", "all"],
    ):
        # references
        me = self.db[str(guild.id)]
        queue = me["queue"]

        if len(queue) > 0:
            voice: VoiceClient = me["current_voice"]
            voice.play(self.music_utils.ffmpeg(queue[0]))


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot=bot))
