import discord
import requests
import asyncio
import os
from random import randint
from dotenv import load_dotenv
import subprocess
from databases import database, server_warn, banned_word
from views import send_target_view, send_help_view, send_meowjam_view, send_kayden_view, get_playing_view, get_queue_view
from audioqueue import audio, audio_queue

# Constants for boolean values
false = False
true = True

load_dotenv()

try:
    token = os.getenv('BOT_TOKEN')
    owner = int(os.getenv('OWNER_ID'))
except:
    print("Error loading environment variables")
    exit(1)

# Set debug mode
debug = False

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client=client)

db = database()

with open("txt_files\\help.txt", "r") as file:
    helpList = file.readlines()

with open("txt_files\\meowjam_quotes.txt", "r") as file:
    meowjamList = file.readlines()

with open("txt_files\\kayden_quotes.txt", "r") as file:
    kaydenList = file.readlines()
    
with open("txt_files\\audiohelp.txt", "r") as file:
    audioHelp = file.readlines()

#helper funtions
def is_toilet_man(word : str) -> bool:
    return "skibidi" in word.lower()

#start up event

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

    try:
        owner_user = client.get_user(owner)
        await owner_user.send(f"{client.user.name} On")
        synced = await tree.sync()
        print(f"synced {len(synced)} commands")
    except Exception as e:
        print(f"on_ready error: {e}")

#public app commands

#hello
@tree.command(name="hello", description="Say Hello")
@discord.app_commands.allowed_installs(guilds=true, users=true)
@discord.app_commands.allowed_contexts(guilds=true, dms=true, private_channels=true)
async def hello(interaction : discord.Interaction):
    await interaction.response.send_message(f"Hey, {interaction.user.mention}")

#say
@tree.command(name="say", description="say something using the bot")
@discord.app_commands.allowed_installs(guilds=true, users=true)
@discord.app_commands.allowed_contexts(guilds=true, dms=true, private_channels=true)
@discord.app_commands.describe(message = "Message to say")
async def say(interaction : discord.Interaction, message : str):
    if db.is_word_banned(message, interaction.guild.id):
        await interaction.response.send_message(f"{interaction.user.mention}, your message contains a banned word and cannot be sent.", ephemeral=true)
        return
    if is_toilet_man(message):
        await interaction.response.send_message(f"{interaction.user.mention}, your message contains a reference to the toilet man and cannot be sent.", ephemeral=true)
        return
    await interaction.response.send_message(message)

#help
@tree.command(name="help", description="lists the help menu")
@discord.app_commands.allowed_installs(guilds=true, users=true)
@discord.app_commands.allowed_contexts(guilds=true, dms=true, private_channels=true)
async def help_menu(interaction : discord.Interaction):
    embed = send_help_view(helpList)
    await interaction.response.send_message(embed=embed)

#meowjam
@tree.command(name="meowjam", description="sends a random meowjam quote")
@discord.app_commands.allowed_installs(guilds=true, users=true)
@discord.app_commands.allowed_contexts(guilds=true, dms=true, private_channels=true)
async def meowjam(interaction : discord.Interaction):
    embed = send_meowjam_view(quote=meowjamList[randint(0, len(meowjamList) - 1)])
    await interaction.response.send_message(embed=embed)

#kayden
@tree.command(name="kayden", description="sends a random kayden quote")
@discord.app_commands.allowed_installs(guilds=true, users=true)
@discord.app_commands.allowed_contexts(guilds=true, dms=true, private_channels=true)
async def kayden(interaction : discord.Interaction):
    embed = send_kayden_view(quote=kaydenList[randint(0, len(kaydenList) - 1)])
    await interaction.response.send_message(embed=embed)

#Rust command - uses steam api to see if caveman is playing rust, only works if caveman is online
@tree.command(name = "rust", description="see if caveman is playing rust.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def rust(interaction : discord.Interaction):
    response = requests.get("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=1402FDF4510AECCDD551943FAC302DC8&steamids=76561198968685475")
    if response.status_code == 200:
        try:
            x = response.json()
            y = x["response"]["players"]
            if y[0]["gameextrainfo"] == "Rust":
                j = y[0]["gameextrainfo"]
                await interaction.response.send_message(f"Caveman is playing Rust")
            else:
                await interaction.response.send_message(f"Caveman is playing something else not rust, he is playing {j}")
        except:
            await interaction.response.send_message("Caveman is not playing any games")

#see what a steam user is playing given a steam id
@tree.command(name = "steamuserplaying", description="Using someones steam id find out if they are playing a game")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.describe(steamid = "The steam id of the user you want to see")
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def steamUserPlaying(interaction : discord.Interaction, steamid : str):
    response = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=1402FDF4510AECCDD551943FAC302DC8&steamids={steamid}")
    if response.status_code == 200:
        x = response.json()
        name = x["response"]["players"][0]["personaname"]
        try:
            y = x["response"]["players"]
            j = y[0]["gameextrainfo"]
  
                
            await interaction.response.send_message(f"{name} is playing {j}")
        except:
            await interaction.response.send_message(f"{name} is not playing anything")
    else:
        await interaction.response.send_message("No user with that Id exists")

#guild commands

@tree.command(name="audiohelp", description="Get help with audio commands")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
async def audio_help(interaction : discord.Interaction):
    embed = send_help_view(audioHelp)
    await interaction.response.send_message(embed=embed)

#kick
@tree.command(name="kick", description="kick a user from the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(kick_members=true)
@discord.app_commands.describe(user="User to kick", reason="Reason for kicking the user")
async def kick(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    if interaction.user.id == user.id:
        await interaction.response.send_message("You cannot kick yourself!", ephemeral=true)
        return
    if interaction.user.guild_permissions.administrator or  interaction.user.top_role <= user.top_role:
        await interaction.response.send_message("You cannot kick a user with a higher or equal role than you.", ephemeral=true)
        return
    try:
        await interaction.guild.kick(user, reason=reason)
        await interaction.response.send_message(f"{user.mention} has been kicked for: {reason}")
        await send_target_view(target=user, target_type="kicked", reason=reason, server=interaction.guild)
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to kick this user.", ephemeral=true)

#ban
@tree.command(name="ban", description="ban a user from the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(ban_members=true)
@discord.app_commands.describe(user="User to ban", reason="Reason for banning the user")
async def ban(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    if interaction.user.id == user.id:
        await interaction.response.send_message("You cannot ban yourself!", ephemeral=true)
        return
    if interaction.user.guild_permissions.administrator or  interaction.user.top_role <= user.top_role:
        await interaction.response.send_message("You cannot ban a user with a higher or equal role than you.", ephemeral=true)
        return
    try:
        await interaction.guild.ban(user, reason=reason)
        await interaction.response.send_message(f"{user.mention} has been banned for: {reason}")
        await send_target_view(target=user, target_type="banned", reason=reason, server=interaction.guild)
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to ban this user.", ephemeral=true)

#unban      
@tree.command(name="unban", description="unban a user from the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(ban_members=true)
@discord.app_commands.describe(user="User to unban", reason="Reason for unbanning the user")
async def unban(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    if interaction.user.id == user.id:
        await interaction.response.send_message("You cannot unban yourself!", ephemeral=true)
        return
    try:
        await interaction.guild.unban(user, reason=reason)
        await interaction.response.send_message(f"{user.mention} has been unbanned for: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to unban this user.", ephemeral=true)

#warn  
@tree.command(name="warn", description="warn a user in the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(manage_messages=true)
@discord.app_commands.describe(user="User to warn", reason="Reason for warning the user")
async def warn(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    if interaction.user.id == user.id:
        await interaction.response.send_message("You cannot warn yourself!", ephemeral=true)
        return
    if interaction.user.guild_permissions.administrator or  interaction.user.top_role <= user.top_role:
        await interaction.response.send_message("You cannot warn a user with a higher or equal role than you.", ephemeral=true)
        return
    try:
        db.add_warn(server_warn(server_id=interaction.guild.id, user_id=user.id))
        await send_target_view(target=user, target_type="warned", reason=reason, server=interaction.guild)
        await interaction.response.send_message(f"{user.mention} has been warned for: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to warn this user.", ephemeral=true)
        
#remove warn
@tree.command(name="removewarn", description="remove a warn from a user in the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(manage_messages=true)
@discord.app_commands.describe(user="User to remove warn from", reason="Reason for removing the warn")
async def remove_warn(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    if interaction.user.id == user.id:
        await interaction.response.send_message("You cannot remove a warn from yourself!", ephemeral=true)
        return
    if interaction.user.guild_permissions.administrator or interaction.user.top_role <= user.top_role:
        await interaction.response.send_message("You cannot remove a warn from a user with a higher or equal role than you.", ephemeral=true)
        return
    try:
        if db.remove_warn(server_warn(server_id=interaction.guild.id, user_id=user.id, count=1)):
            await interaction.response.send_message(f"{user.mention} has had their warn removed for: {reason}")
        else:
            await interaction.response.send_message(f"{user.mention} has no warns to remove.", ephemeral=true)
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to remove a warn from this user.", ephemeral=true)
        
@tree.command(name="warns", description="check the number of warns a user has in the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.describe(user="User to check warns for")
async def warns(interaction : discord.Interaction, user: discord.User):
    warn_data = db.get_warns(server_id=interaction.guild.id, user_id=user.id)
    if warn_data:
        await interaction.response.send_message(f"{user.mention} has {warn_data.count} warns in this server.")
    else:
        await interaction.response.send_message(f"{user.mention} has no warns in this server.")
    
#purge messages
@tree.command(name="purge", description="purge messages in the channel")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(manage_messages=true)
@discord.app_commands.describe(amount="Number of messages to purge")
async def purge(interaction : discord.Interaction, amount: int):
    if amount < 1 or amount > 1000:
        await interaction.response.send_message("You can only purge between 1 and 100 messages.", ephemeral=true)
        return
    
    messages = []
    async for message in interaction.channel.history(limit=amount):
        # Filter out messages that are older than 14 days
        if (discord.utils.utcnow() - message.created_at).days < 14:
            messages.append(message)

    if not messages:
        await interaction.followup.send("No messages to delete!!!", ephemeral=True)
        return
    
    try:
        for i in range(0, len(messages), 100):  # Discord API allows bulk delete of 2-100 messages per call
            chunk = messages[i:i + 100]
            await interaction.channel.delete_messages(chunk)
        await interaction.followup.send(f"Purged {len(messages)} messages.")
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to purge messages in this channel.", ephemeral=true)
        
#banned words commands

@tree.command(name="addbannedword", description="Add a banned word to the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(manage_messages=true)
@discord.app_commands.describe(word="Word to ban")
async def add_banned_word(interaction : discord.Interaction, word: str):
    if db.add_banned_word(banned_word(word=word.upper(), server_id=interaction.guild.id)):
        await interaction.response.send_message(f"has been added to the banned words list.", ephemeral=true)
    else:
        await interaction.response.send_message(f"is already banned in this server.", ephemeral=true)
        
@tree.command(name="removebannedword", description="Remove a banned word from the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(manage_messages=true)
@discord.app_commands.describe(word="Word to remove from banned words list")
async def remove_banned_word(interaction : discord.Interaction, word: str):
    if db.remove_banned_word(word=word.upper(), server_id=interaction.guild.id):
        await interaction.response.send_message(f"has been removed from the banned words list.", ephemeral=true)
    else:
        await interaction.response.send_message(f"is not banned in this server.", ephemeral=true)

@tree.command(name="iswordbanned", description="Check if a word is banned in the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.describe(word="Word to check if it is banned")
async def is_word_banned(interaction : discord.Interaction, word: str):
    if db.is_word_banned(word=word.upper(), server_id=interaction.guild.id):
        await interaction.response.send_message(f"is banned in this server.", ephemeral=true)
    else:
        await interaction.response.send_message(f"is not banned in this server.", ephemeral=true)
        
#remove all banned words
@tree.command(name="removeallbannedwords", description="Remove all banned words from the server")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.checks.has_permissions(manage_messages=true)
async def remove_all_banned_words(interaction : discord.Interaction):
    db.banned_words_collection.delete_many({'server_id': interaction.guild.id})
    await interaction.response.send_message("All banned words have been removed from this server.", ephemeral=true)
    
#music commands

audio_formats = ["mp3", "wav", "ogg", "flac", "aac", "m4a", "opus", "mov", "mp4", "webm"]

def is_audio_file(filename: str) -> bool:
    """Check if the file is an audio file based on its extension."""
    return any(filename.lower().endswith(f".{fmt}") for fmt in audio_formats)

def is_discord_audio_link(url: str) -> bool:
    """Check if the URL is a valid Discord audio link."""
    return url.startswith("https://cdn.discordapp.com/")

def get_discord_name(url: str) -> str:
    lastmark = url.rfind("?")
    firstslash = url.find("/", 65)
    return url[firstslash+1:lastmark]

audioQueueDict : dict[int : audio_queue] = {}

def play_next(guild_id : int):
    """Play the next audio in the queue for the given guild."""
    audio_queue = audioQueueDict.get(guild_id)
    voice_client = discord.utils.get(client.voice_clients, guild__id=guild_id)
    voice_channel = voice_client.channel
    #leave the voice channel if the bot is the only one in it
    if voice_client and len(voice_channel.members) == 1:
        asyncio.run_coroutine_threadsafe(audio_queue.channel.send("Leaving voice channel as I am the only one here."), client.loop)
        asyncio.run_coroutine_threadsafe(voice_client.disconnect(), client.loop)
        return
    if audio_queue is None or (audio_queue and audio_queue.is_empty()):
        asyncio.run_coroutine_threadsafe(audio_queue.channel.send("Leaving voice channel as the queue is empty."), client.loop)
        asyncio.run_coroutine_threadsafe(voice_client.disconnect(), client.loop)
        return
    if audio_queue and not audio_queue.is_empty():
        next_audio = audio_queue.get_next_audio()
        if next_audio:
            if voice_client and not voice_client.is_playing() and not voice_client.is_paused():
                source = discord.FFmpegPCMAudio(next_audio.video)
                voice_client.play(source, after=lambda e: play_next(guild_id))

async def play_audio(url : audio, interaction: discord.Interaction):
    """Play audio in the voice channel."""
    voice_client : discord.VoiceClient = discord.utils.get(client.voice_clients, guild=interaction.guild)
    
    if voice_client == None:
        voice_client = await interaction.user.voice.channel.connect()
    elif voice_client.channel != interaction.user.voice.channel:
        await voice_client.disconnect()
        voice_client = await interaction.user.voice.channel.connect()
    
    if not voice_client.is_playing() and not voice_client.is_paused():
        audio_queue = audioQueueDict.get(interaction.guild.id)
        if audio_queue and not audio_queue.is_empty():
            next_audio = audio_queue.get_next_audio()
            if next_audio:
                source = discord.FFmpegPCMAudio(next_audio.video)
                voice_client.play(source, after=lambda e: play_next(interaction.guild.id))

@tree.command(name="play", description="Play audio in a voice channel")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.describe(url="URL of the audio to play (must be a discord link)")
async def play(interaction : discord.Interaction, url: str):
    voice_client : discord.VoiceClient = discord.utils.get(client.voice_clients, guild=interaction.guild)
    
    if interaction.user.voice is None:
        await interaction.response.send_message("You must be in a voice channel to use this command.", ephemeral=True)
        return
   
    try:
        await interaction.response.defer(thinking=True)
        
        if not is_discord_audio_link(url):
            await interaction.followup.send("The provided URL is not a valid Discord audio link.", ephemeral=True)
            return
        
        file = audio(url=url, _type="discord", name=get_discord_name(url))
        
        if interaction.guild.id not in audioQueueDict:
            audioQueueDict[interaction.guild.id] = audio_queue()
        audioQueue = audioQueueDict[interaction.guild.id]
        audioQueue.channel = interaction.channel
        
        if audioQueue.add_audio(file):
            if voice_client is not None and (voice_client.is_playing() or voice_client.is_paused()):
                await interaction.followup.send(f"Added {file.name} to the audio queue.", ephemeral=True)
            else:
                embed = get_playing_view(text=file.name)
                await interaction.followup.send(embed=embed)
                await play_audio(file, interaction)
        else:
            await interaction.followup.send("The audio queue is full. Please wait for the current audio to finish before adding more.", ephemeral=True)
            return
    except Exception as e:
        print(f"Error in play command: {e}")
        await interaction.followup.send("An error occurred while trying to play the audio. Please check the URL and try again.", ephemeral=True)

@tree.command(name="skip", description="Skip the current audio in the voice channel")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
@discord.app_commands.describe(position="Position in the queue to skip to (0 for next audio)")
async def skip(interaction : discord.Interaction, position: int = 0):
    voice_client : discord.VoiceClient = discord.utils.get(client.voice_clients, guild=interaction.guild)
    
    await interaction.response.defer(thinking=True)
    if voice_client and voice_client.is_connected():
        audio_queue = audioQueueDict.get(interaction.guild.id)
        
        if audio_queue.is_empty():
            await interaction.followup.send("The audio queue is empty.", ephemeral=True)
            return
        audio : 'audio' = audio_queue.pop_at_position(position)
        voice_client.stop()
        embed = get_playing_view(text=audio.name)
        await interaction.followup.send(embed=embed)
        await play_audio(audio, interaction)
    else:
        await interaction.followup.send("I am not connected to a voice channel.", ephemeral=True)
        return   
    
@tree.command(name="pause", description="Pause the current audio in the voice channel")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
async def pause(interaction : discord.Interaction):
    voice_client : discord.VoiceClient = discord.utils.get(client.voice_clients, guild=interaction.guild)
    
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("Paused the current audio.", ephemeral=True)
    else:
        await interaction.response.send_message("No audio is currently playing.", ephemeral=True)
        
@tree.command(name="resume", description="Resume the paused audio in the voice channel")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
async def resume(interaction : discord.Interaction):
    voice_client : discord.VoiceClient = discord.utils.get(client.voice_clients, guild=interaction.guild)
    
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("Resumed the paused audio.", ephemeral=True)
    else:
        await interaction.response.send_message("No audio is currently paused.", ephemeral=True)
        
@tree.command(name="stop", description="Stop the current audio in the voice channel")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
async def stop(interaction : discord.Interaction):
    voice_client : discord.VoiceClient = discord.utils.get(client.voice_clients, guild=interaction.guild)
    
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        audio_queue = audioQueueDict.get(interaction.guild.id)
        if audio_queue:
            audio_queue.reset()
        await interaction.response.send_message("Stopped the current audio and cleared the queue.", ephemeral=True)
    else:
        await interaction.response.send_message("No audio is currently playing or paused.", ephemeral=True)
        
@tree.command(name="queue", description="View the current audio queue")
@discord.app_commands.allowed_installs(guilds=true, users=false)
@discord.app_commands.allowed_contexts(guilds=true, dms=false, private_channels=false)
async def queue(interaction : discord.Interaction):
    voice_client : discord.VoiceClient = discord.utils.get(client.voice_clients, guild=interaction.guild)
    
    if voice_client and voice_client.is_connected():
        audio_queue = audioQueueDict.get(interaction.guild.id)
        
        if audio_queue and not audio_queue.is_empty():
            current_audio = audio_queue.current.name if audio_queue.current else "None"
            embed = get_queue_view(queue=audio_queue.queue, current=current_audio)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("The audio queue is empty.", ephemeral=True)
    else:
        await interaction.response.send_message("I am not connected to a voice channel.", ephemeral=True)

#message events

@client.event
async def on_message(message : discord.Message):
    if message.author == client.user:
        return

    if message.author.id == owner:
        if message.content.startswith("!restart"):
            await message.channel.send("Restarting bot...")
            subprocess.run(["restart.bat"], shell=True)
            return
            
        elif message.content.startswith("!debug"):
            global debug
            debug = not debug
            await message.channel.send(f"Debug mode is now {'on' if debug else 'off'}", ephemeral=True)
    
    #scan message content
    try:
        if message.content != "" and len(message.content) > 2:
            if db.does_word_contain_banned_word(message.content.upper(), message.guild.id):
                await message.delete()
                return
            elif is_toilet_man(message.content):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, your message contained a reference to the toilet man",)
                return
        elif message.attachments:
            for attachment in message.attachments:
                if db.is_word_banned(attachment.filename, message.guild.id):
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, your attachment is banned and has been deleted.", ephemeral=True)
                    return
    except Exception as e:
        print(f"Error in on_message: {e}")

client.run(token)