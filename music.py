import discord
from discord.ext import commands
import youtube_dl
import asyncio
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class music(commands.Cog):
    def __init__(self,bot) -> None:
        self.bot=bot

    @commands.command()
    async def join(self,ctx):
        if not ctx.author.voice:
            return await ctx.send("You're not in a Voice channel!")

        voice = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice.connect()
        else:
            await ctx.voice_client.move_to(voice)

    @commands.command()
    async def leave(self,ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self,ctx,*,url):
        
        if not ctx.author.voice:
            return await ctx.send("You're not in a Voice channel!")

        voice = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice.connect()
        else:
            await ctx.voice_client.move_to(voice)
        ctx.voice_client.stop()

        FFMPEG_OPTIONS = {"before_options":"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options":"-vn"}

        YTDL_OPTIONS = {"format":"bestaudio"}
        print(url)
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def stop(self,ctx):
        await ctx.voice_client.stop()
        
    @commands.command()
    async def pause(self,ctx):
        await ctx.voice_client.pause()
        
    @commands.command()
    async def resume(self,ctx):
        await ctx.voice_client.pause()


def setup(bot):
    bot.add_cog(music(bot))
