import asyncio
import discord
import requests
import os
from random import randint
from dotenv import load_dotenv
from databases import database, server_warn, banned_word, server_setting
from views import send_target_view, send_help_view, send_meowjam_view, send_kayden_view, error_embed
from help_text import help_list, kayden_quote_list, meowjam_quote_list

load_dotenv()

try:
    token = os.getenv('BOT_TOKEN')
    owner = int(os.getenv('OWNER_ID'))
    steam_key= os.getenv('Steam_API_Key')
except:
    print("Error loading environment variables")
    exit(1)

# Set debug mode
debug = False

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client=client)

db = database()

#helper funtions
def is_toilet_man(word : str) -> bool:
    return "skibidi" in word.lower()

async def on_error_custom(e, function_name : str = "Unknown"):
    error_message = f"An error occurred in function '{function_name}': `{e}`"
    print(error_message)
    if debug:
        await client.get_user(owner).send(error_message, silent=True)
    
#start up event

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    try:
        owner_user = client.get_user(owner)
        await owner_user.send(f"{client.user.name} On, Debug mode is {'on' if debug else 'off'}", silent=True)
        synced = await tree.sync()
        print(f"synced {len(synced)} commands")
    except Exception as e:
        print(f"on_ready error: {e}")

#public app commands

#hello
@tree.command(name="hello", description="Say Hello")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hello(interaction : discord.Interaction):
    try:
        await interaction.response.send_message(f"Hey, {interaction.user.mention}")
    except Exception as e:
        print(f"Error in hello command: {e}")
        await on_error_custom(e, "Hello Command")
        await interaction.response.send_message("An error occurred while trying to say hello. Please try again.", ephemeral=True)

#say
@tree.command(name="say", description="say something using the bot")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.describe(message = "Message to say")
async def say(interaction : discord.Interaction, message : str):
    try:
        if db.is_word_banned(message, interaction.guild.id):
            await interaction.response.send_message(f"{interaction.user.mention}, your message contains a banned word and cannot be sent.", ephemeral=True)
            return
        if is_toilet_man(message):
            await interaction.response.send_message(f"{interaction.user.mention}, your message contains a reference to the toilet man and cannot be sent.", ephemeral=True)
            return
        await interaction.response.send_message(message)
    except Exception as e:
        print(f"Error in say command: {e}")
        await on_error_custom(e, "Say Command")
        embed = error_embed("An error occurred while trying to send your message.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#help
@tree.command(name="help", description="lists the help menu")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def help_menu(interaction : discord.Interaction):
    try:
        embed = send_help_view(help_list)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in help_menu command: {e}")
        await on_error_custom(e, "Help Menu Command")
        embed = error_embed("An error occurred while trying to get the help menu.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#meowjam
@tree.command(name="meowjam", description="sends a random meowjam quote")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def meowjam(interaction : discord.Interaction):
    try:
        embed = send_meowjam_view(quote=meowjam_quote_list[randint(0, len(meowjam_quote_list) - 1)])
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in meowjam command: {e}")
        await on_error_custom(e, "MeowJam Command")
        embed= error_embed("An error occurred while trying to get a MeowJam quote.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#kayden
@tree.command(name="kayden", description="sends a random kayden quote")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def kayden(interaction : discord.Interaction):
    try:
        embed = send_kayden_view(quote=kayden_quote_list[randint(0, len(kayden_quote_list) - 1)])
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in kayden command: {e}")
        await on_error_custom(e, "Kayden Command")
        embed= error_embed("An error occurred while trying to get a Kayden quote.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def fetch_steam_user_playing(steamid: str) -> tuple[str, bool]:
    """Return (message, ephemeral) for a Steam user's current game."""
    try:
        response = await asyncio.to_thread(
            requests.get,
            f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_key}&steamids={steamid}",
            timeout=10,
        )
        if response.status_code != 200:
            return "Failed to fetch data from Steam API", True

        payload = response.json()
        players = payload.get("response", {}).get("players", [])
        if not players:
            return "No user with that Id exists", True

        player = players[0]
        name = player.get("personaname", "Unknown User")
        game = player.get("gameextrainfo")
        if game:
            return f"{name} is playing {game}", False
        return f"{name} is not playing anything", False

    except Exception as e:
        await on_error_custom(e, "fetch_steam_user_playing")
        return "There was an error retrieving the user's game status.", True

#Rust command - uses steam api to see if caveman is playing rust, only works if caveman is online
@tree.command(name = "rust", description="see if caveman is playing rust.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def rust(interaction : discord.Interaction):
    message, ephemeral = await fetch_steam_user_playing("76561198968685475")
    await interaction.response.send_message(message, ephemeral=ephemeral)
        
#see what a steam user is playing given a steam id
@tree.command(name = "steamuserplaying", description="Using someones steam id find out if they are playing a game")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.describe(steamid = "The steam id of the user you want to see")
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def steamuserplaying_command(interaction : discord.Interaction, steamid : str):
    message, ephemeral = await fetch_steam_user_playing(steamid)
    await interaction.response.send_message(message, ephemeral=ephemeral)

#guild commands

#kick
@tree.command(name="kick", description="kick a user from the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(kick_members=True)
@discord.app_commands.describe(user="User to kick", reason="Reason for kicking the user")
async def kick(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    try:
        if interaction.user.id == user.id:
            await interaction.response.send_message("You cannot kick yourself!", ephemeral=True)
            return
        if (not interaction.user.guild_permissions.administrator) and interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot kick a user with a higher or equal role than you.", ephemeral=True)
            return
        try:
            await interaction.guild.kick(user, reason=reason)
            await interaction.response.send_message(f"{user.mention} has been kicked for: {reason}")
            await send_target_view(target=user, target_type="kicked", reason=reason, server=interaction.guild)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to kick this user.", ephemeral=True)
    except Exception as e:
        print(f"Error in kick command: {e}")
        await on_error_custom(e, "kick command")
        embed = error_embed("An error occurred while trying to kick the user. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#ban
@tree.command(name="ban", description="ban a user from the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(ban_members=True)
@discord.app_commands.describe(user="User to ban", reason="Reason for banning the user")
async def ban(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    try:
        if interaction.user.id == user.id:
            await interaction.response.send_message("You cannot ban yourself!", ephemeral=True)
            return
        if (not interaction.user.guild_permissions.administrator) and interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot ban a user with a higher or equal role than you.", ephemeral=True)
            return
        try:
            await interaction.guild.ban(user, reason=reason)
            await interaction.response.send_message(f"{user.mention} has been banned for: {reason}")
            await send_target_view(target=user, target_type="banned", reason=reason, server=interaction.guild)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to ban this user.", ephemeral=True)
    except Exception as e:
        print(f"Error in ban command: {e}")
        await on_error_custom(e, "ban command")
        embed = error_embed("An error occurred while trying to ban the user. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#unban      
@tree.command(name="unban", description="unban a user from the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(ban_members=True)
@discord.app_commands.describe(user="User to unban", reason="Reason for unbanning the user")
async def unban(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    try:
        if interaction.user.id == user.id:
            await interaction.response.send_message("You cannot unban yourself!", ephemeral=True)
            return
        try:
            await interaction.guild.unban(user, reason=reason)
            await interaction.response.send_message(f"{user.mention} has been unbanned for: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to unban this user.", ephemeral=True)
    except Exception as e:
        print(f"Error in unban command: {e}")
        await on_error_custom(e, "unban command")
        embed = error_embed("An error occurred while trying to unban the user. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#warn  
@tree.command(name="warn", description="warn a user in the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(user="User to warn", reason="Reason for warning the user")
async def warn(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    try:
        if interaction.user.id == user.id:
            await interaction.response.send_message("You cannot warn yourself!", ephemeral=True)
            return
        if (not interaction.user.guild_permissions.administrator) and interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot warn a user with a higher or equal role than you.", ephemeral=True)
            return
        try:
            db.add_warn(server_warn(server_id=interaction.guild.id, user_id=user.id))
            await send_target_view(target=user, target_type="warned", reason=reason, server=interaction.guild)
            await interaction.response.send_message(f"{user.mention} has been warned for: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to warn this user.", ephemeral=True)
    except Exception as e:
        print(f"Error in warn command: {e}")
        await on_error_custom(e, "warn command")
        embed = error_embed("An error occurred while trying to warn the user. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
#remove warn
@tree.command(name="removewarn", description="remove a warn from a user in the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(user="User to remove warn from", reason="Reason for removing the warn")
async def remove_warn(interaction : discord.Interaction, user: discord.User, reason: str = "No reason provided"):
    try:
        if interaction.user.id == user.id:
            await interaction.response.send_message("You cannot remove a warn from yourself!", ephemeral=True)
            return
        if (not interaction.user.guild_permissions.administrator) and interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot remove a warn from a user with a higher or equal role than you.", ephemeral=True)
            return
        try:
            if db.remove_warn(server_warn(server_id=interaction.guild.id, user_id=user.id)):
                await interaction.response.send_message(f"{user.mention} has had their warn removed for: {reason}")
            else:
                await interaction.response.send_message(f"{user.mention} has no warns to remove.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to remove a warn from this user.", ephemeral=True)
    except Exception as e:
        print(f"Error in remove_warn command: {e}")
        await on_error_custom(e, "remove_warn command")
        embed = error_embed("An error occurred while trying to remove the warn. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
@tree.command(name="warns", description="check the number of warns a user has in the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.describe(user="User to check warns for")
async def warns(interaction : discord.Interaction, user: discord.User):
    try:
        warn_data = db.get_warns(server_id=interaction.guild.id, user_id=user.id)
        if warn_data:
            await interaction.response.send_message(f"{user.mention} has {warn_data.count} warns in this server.")
        else:
            await interaction.response.send_message(f"{user.mention} has no warns in this server.")
    except Exception as e:
        print(f"Error in warns command: {e}")
        await on_error_custom(e, "warns command")
        embed = error_embed("An error occurred while trying to check the user's warns.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
#purge messages
@tree.command(name="purge", description="purge messages in the channel")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(amount="Number of messages to purge")
async def purge(interaction : discord.Interaction, amount: int):
    try:
        if amount < 1 or amount > 100:
            await interaction.response.send_message("You can only purge between 1 and 100 messages.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
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
            await interaction.followup.send(f"Purged {len(messages)} messages.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I do not have permission to purge messages in this channel.", ephemeral=True)
    except Exception as e:
        print(f"Error in purge command: {e}")
        await on_error_custom(e, "purge command")
        embed = error_embed("An error occurred while trying to purge messages. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
#banned words commands

@tree.command(name="add_audit_log_channel", description="Set the channel for audit logs")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(channel="Channel to set as audit log channel")
async def add_audit_log_channel(interaction : discord.Interaction, channel: discord.TextChannel):
    try:
        result = db.get_server_setting(interaction.guild.id)
        if result is None:
            db.add_server_setting(server_setting(server_id=interaction.guild.id, audit_channel=channel.id))
            cached_server_settings[interaction.guild.id] = server_setting(server_id=interaction.guild.id, audit_channel=channel.id)
        else:
            result.audit_channel = channel.id
            db.edit_server_setting(result)
            cached_server_settings[interaction.guild.id] = result
        await interaction.response.send_message(f"{channel.mention} has been set as the audit log channel.", ephemeral=True)
    except Exception as e:
        await on_error_custom(e, "add_audit_log_channel command")
        embed = error_embed("An error occurred while trying to set the audit log channel. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="remove_audit_log_channel", description="Remove the audit log channel")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def remove_audit_log_channel(interaction : discord.Interaction):
    try:
        result = db.get_server_setting(interaction.guild.id)
        if result is not None:
            result.audit_channel = None
            db.edit_server_setting(result)
            cached_server_settings[interaction.guild.id] = result
        await interaction.response.send_message("The audit log channel has been removed.", ephemeral=True)
    except Exception as e:
        await on_error_custom(e, "remove_audit_log_channel command")
        embed = error_embed("An error occurred while trying to remove the audit log channel. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="random_number", description="Generate a random number between two numbers")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.describe(min="Minimum number", max="Maximum number")
async def random_number(interaction : discord.Interaction, min: int, max: int):
    try:
        if min > max:
            await interaction.response.send_message("Minimum number cannot be greater than maximum number.", ephemeral=True)
            return
        number = randint(min, max)
        await interaction.response.send_message(f"Your random number between {min} and {max} is: {number}")
    except Exception as e:
        await on_error_custom(e, "random_number command")
        embed = error_embed("An error occurred while trying to generate a random number. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="toggle_auto_moderation", description="Toggle auto moderation on or off")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def toggle_auto_moderation(interaction : discord.Interaction):
    try:
        result = db.get_server_setting(interaction.guild.id)
        if result is None:
            db.add_server_setting(server_setting(server_id=interaction.guild.id, auto_moderation=True))
            cached_server_settings[interaction.guild.id] = server_setting(server_id=interaction.guild.id, auto_moderation=True)
            await interaction.response.send_message("Auto moderation has been turned on.", ephemeral=True)
        else:
            result.auto_moderation = not result.auto_moderation
            db.edit_server_setting(result)
            cached_server_settings[interaction.guild.id] = result
            await interaction.response.send_message(f"Auto moderation has been turned {'on' if result.auto_moderation else 'off'}.", ephemeral=True)
    except Exception as e:
        await on_error_custom(e, "toggle_auto_moderation command")
        embed = error_embed("An error occurred while trying to toggle auto moderation. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="addbannedword", description="Add a banned word to the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(word="Word to ban")
async def add_banned_word(interaction : discord.Interaction, word: str):
    try:
        upper_word = word.upper()
        if db.add_banned_word(banned_word(word=upper_word, server_id=interaction.guild.id)):
            await interaction.response.send_message(f"{word} has been added to the banned words list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{word} is already banned in this server.", ephemeral=True)
    except Exception as e:
        print(f"Error in add_banned_word: {e}")
        await on_error_custom(e, "add_banned_word")
        embed = error_embed("An error occurred while trying to add the banned word. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
@tree.command(name="removebannedword", description="Remove a banned word from the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(word="Word to remove from banned words list")
async def remove_banned_word(interaction : discord.Interaction, word: str):
    try:
        upper_word = word.upper()
        if db.remove_banned_word(word=upper_word, server_id=interaction.guild.id):
            await interaction.response.send_message(f"{word} has been removed from the banned words list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{word} is not banned in this server.", ephemeral=True)
    except Exception as e:
        print(f"Error in remove_banned_word: {e}")
        await on_error_custom(e, "remove_banned_word")
        embed = error_embed("An error occurred while trying to remove the banned word. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="iswordbanned", description="Check if a word is banned in the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.describe(word="Word to check if it is banned")
async def is_word_banned(interaction : discord.Interaction, word: str):
    try:
        upper_word = word.upper()
        if db.is_word_banned(word=upper_word, server_id=interaction.guild.id):
            await interaction.response.send_message(f"{upper_word} is banned in this server.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{upper_word} is not banned in this server.", ephemeral=True)
    except Exception as e:
        print(f"Error in is_word_banned: {e}")
        await on_error_custom(e, "is_word_banned")
        embed = error_embed("An error occurred while trying to check if the word is banned. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
#remove all banned words
@tree.command(name="removeallbannedwords", description="Remove all banned words from the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def remove_all_banned_words(interaction : discord.Interaction):
    try:
        db.banned_words_collection.delete_many({'server_id': interaction.guild.id})
        await interaction.response.send_message("All banned words have been removed from this server.", ephemeral=True)
    except Exception as e:
        print(f"Error in remove_all_banned_words: {e}")
        await on_error_custom(e, "remove_all_banned_words")
        embed = error_embed("An error occurred while trying to remove all banned words. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#client events

cached_server_settings = {}

def is_media(message : discord.Message) -> bool:
    if message.attachments:
        return True
    if message.embeds:
        return True
    if message.content:
        if "http://" in message.content.lower() or "https://" in message.content.lower():
            return True
        if "GIF" in message.content.upper():
            return True
    return False

def get_server_settings(guild_id):
    if guild_id in cached_server_settings:
        return cached_server_settings[guild_id]
    
    result = db.get_server_setting(guild_id)
    cached_server_settings[guild_id] = result
    return result

@client.event
async def on_message_edit(before : discord.Message, after : discord.Message):
    if before.author == client.user:
        return
    
    if is_media(after):
        return

    result = get_server_settings(before.guild.id)
    if result == None:
        return
    
    if not result.auto_moderation:
        return
    
    if db.does_word_contain_banned_word(after.content.upper(), before.guild.id) or is_toilet_man(after.content):
        await after.delete()

    if result.audit_channel == None:
        return
    
    try:
        audit_channel = client.get_channel(result.audit_channel)
        if audit_channel:
            embed = discord.Embed(title="Message Edited", description=f"{before.author.mention} edited a message in {before.channel.mention}", color=discord.Color.orange())
            embed.add_field(name="Before", value=before.content if before.content else "No content", inline=False)
            embed.add_field(name="After", value=after.content if after.content else "No content", inline=False)
            embed.add_field(name="Jump to Message", value=f"[Click Here]({after.jump_url})", inline=False)
            embed.add_field(name="Edited At", value=after.edited_at if after.edited_at else "Unknown", inline=False)
            await audit_channel.send(embed=embed)
    except Exception as e:
        await on_error_custom(e, "on_message_edit")

@client.event
async def on_message_delete(message : discord.Message):
    if message.author == client.user:
        return

    result = get_server_settings(message.guild.id)
    if result == None:
        return
    
    if result.audit_channel == None:
        return
    
    try:
        audit_channel = client.get_channel(result.audit_channel)
        if audit_channel:
            embed = discord.Embed(title="Message Deleted", description=f"Message by {message.author.mention} was deleted in {message.channel.mention}", color=discord.Color.red())
            if message.attachments:
                embed.add_field(name="Attachments", value="\n".join(attachment.url for attachment in message.attachments), inline=False)
            if message.embeds:
                embed.add_field(name="Embeds", value="\n".join(embed.url for embed in message.embeds if embed.url), inline=False)
            if message.content:
                embed.add_field(name="Content", value=message.content, inline=False)
            else:
                embed.add_field(name="Content", value="No content", inline=False)
            embed.add_field(name="Deleted At", value=discord.utils.utcnow(), inline=False)
            await audit_channel.send(embed=embed)
    except Exception as e:
        await on_error_custom(e, "on_message_delete")

@client.event
async def on_message_bulk_delete(messages : list[discord.Message]):
    if len(messages) == 0:
        return

    result = get_server_settings(messages[0].guild.id)
    if result == None:
        return
    
    if result.audit_channel == None:
        return
    
    try:
        audit_channel = client.get_channel(result.audit_channel)
        if audit_channel:
            embed = discord.Embed(title="Bulk Message Delete", description=f"{len(messages)} messages were deleted in {messages[0].channel.mention}", color=discord.Color.red())
            embed.add_field(name="Deleted At", value=discord.utils.utcnow(), inline=False)
            await audit_channel.send(embed=embed)
    except Exception as e:
        await on_error_custom(e, "on_message_bulk_delete")

@client.event
async def on_member_remove(member : discord.Member):
    result = get_server_settings(member.guild.id)
    if result == None:
        return
    
    if result.audit_channel == None:
        return
    
    try:
        audit_channel = client.get_channel(result.audit_channel)
        if audit_channel:
            embed = discord.Embed(title="Member Left", description=f"{member.mention} has left the server.", color=discord.Color.red())
            embed.add_field(name="Joined At", value=member.joined_at if member.joined_at else "Unknown", inline=False)
            embed.add_field(name="Left At", value=discord.utils.utcnow(), inline=False)
            await audit_channel.send(embed=embed)
    except Exception as e:
        await on_error_custom(e, "on_member_remove")

@client.event
async def on_member_update(before : discord.Member, after : discord.Member):
    if before.guild is None:
        return

    result = get_server_settings(after.guild.id)
    if result == None:
        return
    
    if not result.audit_channel:
        return

    try:
        audit_channel = client.get_channel(result.audit_channel)
        if audit_channel:
            embed = discord.Embed(title="Member Updated", description=f"{before.mention} was updated in {after.guild.name}", color=discord.Color.blue())
            if before.name != after.name:
                embed.add_field(name="Username Changed", value=f"From: {before.name}\nTo: {after.name}", inline=False)
            if before.nick != after.nick:
                embed.add_field(name="Nickname Changed", value=f"From: {before.nick}\nTo: {after.nick}", inline=False)
            if before.roles != after.roles:
                embed.add_field(name="Roles Changed", value=f"Roles changed in {after.mention}", inline=False)
                before_roles = set(before.roles)
                after_roles = set(after.roles)
                added_roles = after_roles - before_roles
                removed_roles = before_roles - after_roles
                if added_roles:
                    embed.add_field(name="Roles Added", value=", ".join(role.name for role in added_roles), inline=False)
                if removed_roles:
                    embed.add_field(name="Roles Removed", value=", ".join(role.name for role in removed_roles), inline=False)
            if before.avatar != after.avatar:
                embed.add_field(name="Avatar Changed", value=f"{after.mention} changed their avatar.", inline=False)
            embed.add_field(name="Updated At", value=discord.utils.utcnow(), inline=False)
            await audit_channel.send(embed=embed)
    except Exception as e:
        await on_error_custom(e, "on_member_update")

@client.event 
async def on_member_ban(guild : discord.Guild, user : discord.Member):
    result = get_server_settings(guild.id)
    if result == None:
        return
    
    if result.audit_channel == None:
        return
    
    try:
        audit_channel = client.get_channel(result.audit_channel)
        if audit_channel:
            embed = discord.Embed(title="Member Banned", description=f"{user.mention} has been banned from the server.", color=discord.Color.red())
            embed.add_field(name="Member since", value=user.joined_at if user.joined_at else "Unknown", inline=False)
            embed.add_field(name="Banned At", value=discord.utils.utcnow(), inline=False)
            await audit_channel.send(embed=embed)
    except Exception as e:
        await on_error_custom(e, "on_member_ban")

@client.event
async def on_member_unban(guild : discord.Guild, user : discord.User):
    result = get_server_settings(guild.id)
    if result == None:
        return
    
    if result.audit_channel == None:
        return
    
    try:
        audit_channel = client.get_channel(result.audit_channel)
        if audit_channel:
            embed = discord.Embed(title="Member Unbanned", description=f"{user.mention} has been unbanned from the server.", color=discord.Color.green())
            embed.add_field(name="Unbanned At", value=discord.utils.utcnow(), inline=False)
            await audit_channel.send(embed=embed)
    except Exception as e:
        await on_error_custom(e, "on_member_unban")

@client.event
async def on_invite_create(invite : discord.Invite):
    result = get_server_settings(invite.guild.id)
    if result == None:
        return
    
    if result.audit_channel == None:
        return
    
    try:
        audit_channel = client.get_channel(result.audit_channel)
        if audit_channel:
            embed = discord.Embed(title="Invite Created", description=f"{invite.inviter.mention} created an invite to {invite.channel.mention}", color=discord.Color.green())
            embed.add_field(name="Invite Code", value=invite.code, inline=False)
            embed.add_field(name="Max Uses", value=invite.max_uses if invite.max_uses else "No limit", inline=False)
            await audit_channel.send(embed=embed)
    except Exception as e:
        await on_error_custom(e, "on_invite_create")

max_rand_number = 50

@client.event
async def on_message(message : discord.Message):
    if message.author == client.user:
        return
    
    if message.author.id == 586246529996816406: #if caveman sends a message, there is a 1 in 50 chance it will be deleted to mess with him
        if randint(1, max_rand_number) == 1:
            await message.delete()
            return

    if message.author.id == owner:
        if message.content.startswith("!debug"):
            global debug
            debug = not debug
            await message.channel.send(f"Debug mode is now {'on' if debug else 'off'}")
            return
        if message.content.startswith("!rand"):
            global max_rand_number
            max_rand_number = int(message.content.split(" ")[1])
            return
    
    if message.guild is None:
        return

    #scan message content
    try:
        result = get_server_settings(message.guild.id)
        if result is None or not result.auto_moderation:
            return
        if message.content != "" and len(message.content) > 2:
            if db.does_word_contain_banned_word(message.content.upper(), message.guild.id):
                await message.delete()
                return
            elif is_toilet_man(message.content):
                await message.delete()
                await message.channel.send(f"{message.author.mention}, your message contained a reference to the toilet man", silent=True)
                return
        elif message.attachments:
            for attachment in message.attachments:
                if db.is_word_banned(attachment.filename.upper(), message.guild.id):
                    await message.delete()
                    return
    except Exception as e:
        print(f"Error in on_message: {e}")
        await on_error_custom(e, "on_message")

@client.event
async def on_error(event, args, kwargs):
    print(f"An error occurred in {event}: {args} {kwargs}")

client.run(token)
