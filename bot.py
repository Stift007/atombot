import datetime
from discord.ext import commands,ipc
import json
from dhooks import Webhook
import asyncio
import random
import os

import discord
from requests.exceptions import RetryError

class Atom(commands.AutoShardedBot):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self.ipc = ipc.Server(self,secret_key="atombot")

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name=f"http://atom.bot down 👀"))
        print("Bot is ready")
        
    async def on_ipc_ready(self):
        print("IPC is ready")

    async def on_ipc_error(self,endpoint,error):
        print(endpoint," raised ",error)


def get_prefix(bot,msg):

    with open("config.json") as f:
        config = json.load(f)

    return config[str(msg.guild.id)]["prefix"]     

client = Atom(command_prefix=get_prefix)
client.remove_command("help")

hook = Webhook("https://discord.com/api/webhooks/895035804089462814/8gEa6NGWeJhn2rE-QYtS4SPAT2VPwAz09GRCppwRY27xOayx6W3WXL0fUqAg_wAm_k0Z")

@client.ipc.route()
async def get_guild_count(data):
    return len(client.guilds)
    
@client.ipc.route()
async def get_guild_ids(data):
    final_ = []
    for guild in client.guilds:
        final_.append(guild.id)

    return final_

sample = {
    "prefix":"a!",
    "has_premium":False,
}

async def cleanupEmbed(embed:discord.Embed):
    embed.set_footer(text="I am a bot and this action was performed automatically. Please contact the moderators of this Bot if you have any questions or concerns")
    return embed


snipe_message_author = {}
snipe_message_content = {}

@client.event
async def on_message_delete(message):
     snipe_message_author[message.channel.id] = message.author
     snipe_message_content[message.channel.id] = message.content
     await asyncio.sleep(60)
     del snipe_message_author[message.channel.id]
     del snipe_message_content[message.channel.id]

@client.command(name = 'snipe')
async def snipe(ctx):
    channel = ctx.channel
    try: #This piece of code is run if the bot finds anything in the dictionary
        em = discord.Embed(name = f"Last deleted message in #{channel.name}", description = snipe_message_content[channel.id])
        em = await cleanupEmbed(em)
        await ctx.send(embed = em)
    except: #This piece of code is run if the bot doesn't find anything in the dictionary
        await ctx.send(f"There are no recently deleted messages in #{channel.name}")


@client.event
async def on_guild_join(guild):
    hook.send(f"Bot Added!\nGuild Name: {guild.name}\nGuild ID: {guild.id}\nGuild Number: {len(client.guilds)}")
    
    with open("config.json") as f:
        config = json.load(f)

    config[str(guild.id)] = sample

    with open("config.json","w+") as f:
        json.dump(config,f)

    for channel in guild.text_channels:
        try:
            embed = discord.Embed(title=":wave: Hello! Glad you decided to add ATOM!")
            embed.description=f"I hope that I can help improving your Server!\n\nCommands: `a!help` or `http://atom.bot/docs/`"
            embed = await cleanupEmbed(embed)
            await channel.send(embed=embed)
            break
        except:
            continue
    


@client.event
async def on_member_join(member):
    with open("levels.json") as f:
        users = json.load(f)

@client.command()
async def invite(ctx):
    await ctx.author.send("Invite ATOM here: :link: https://discord.com/api/oauth2/authorize?client_id=891758172660977725&permissions=536870383095&redirect_uri=http%3A%2F%2F127.0.0.1%3A18253%2Foauth%2Fdiscord&scope=bot%20applications.commands")

@client.command()
@commands.has_permissions(manage_guild=True)
async def prefix(ctx,pre="a!"):
    with open("config.json") as f:
        config = json.load(f)

    config[str(ctx.guild.id)]["prefix"] = pre

    with open("config.json","w+") as f:
        json.dump(config,f)

    embed = discord.Embed(title="Prefix Updated").description=f"Prefix was updated to {pre}"
    embed = await cleanupEmbed(embed)

    await ctx.reply(embed=embed)
    
@client.event
async def on_message(message):
    
    await client.process_commands(message)

@client.group(invoke_without_command=True)
async def help(ctx):
    embed = discord.Embed(title=f"Atom | ")


@client.command()
async def avatar(ctx,member:discord.Member=None):
    if not member:
        member = ctx.author

    embed = discord.Embed(title=member,color=member.color)
    embed.set_image(url=member.avatar_url)
    await ctx.reply(embed=embed)

@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx,amount=1):
    await ctx.channel.purge(limit=amount+1)

@client.command()
@commands.has_permissions(manage_roles=True)
async def gstart(ctx,mins:int,*,prize):
    
    with open("config.json") as f:
        config = json.load(f)
    premium_active = config[str(ctx.guild.id)]["has_premium"]
    if not premium_active:
        return await ctx.reply(f':x: Premium is not active on this Server')


    embed = discord.Embed(title="**Giveaway!**")
    embed.description=prize
    embed.color=ctx.author.color
    tend = datetime.datetime.utcnow() + datetime.timedelta(seconds=mins*60)
    embed = await cleanupEmbed(embed)
    embed.add_field(name="Ends at:",value=f'{tend}, UTC')
    embed.add_field(name="Ends in:",value=f'{mins}, Minutes')

    gmesg = await ctx.send(embed = embed)
    await gmesg.add_reaction("🎉")
    await ctx.message.delete()
    await asyncio.sleep(mins*60)
    
    new_msg = await ctx.channel.fetch_message(gmesg.id)

    users = await new_msg.reactions[0].users().flatten()
    users.pop(users.index(client.user))

    winner = random.choice(users)

    await gmesg.delete()
    await ctx.send(f"Congratulations! {winner.mention} has won!")

@client.group()
async def premium(ctx):
    pass

@premium.command()
async def perks(ctx):
    await ctx.send("**Premium Perks**:\n - Priority Queue\n - 24/7 Music\n - Giveaway System\n")

@premium.command()
async def status(ctx):
    with open("config.json") as f:
        config = json.load(f)
    premium_active = config[str(ctx.guild.id)]["has_premium"]
    await ctx.send(f"**Premium Status on {ctx.guild.name}**:\n {'Active' if premium_active else 'Unactivated!'}")

@premium.command()
async def activate(ctx,*,coupon):
    with open("config.json") as f:
        config = json.load(f)

    if not coupon=="ATOMICP":
        return await ctx.send(":x: Bad Coupon")
    config[str(ctx.guild.id)]["has_premium"] = True
    await ctx.send(":white_check_mark: Okay! Premium has been activated.")
    hook.send(f"{ctx.guild.name} has activated their Premium!")
    with open("config.json","w+") as f:
        json.dump(config,f)

@client.command()
async def help(ctx):
    embed = discord.Embed(title="")

client.ipc.start()
client.run("TOKEN")
