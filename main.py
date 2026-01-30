import discord
import requests
import os
from random import randint
from dotenv import load_dotenv
from databases import database, server_warn, banned_word
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

async def on_error(e):
    if debug:
        await client.get_user(owner).send(f"An error occurred: `{e}`", silent=True)
    
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
        await on_error(e)
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
        await on_error(e)
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
        await on_error(e)
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
        await on_error(e)
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
        await on_error(e)
        embed= error_embed("An error occurred while trying to get a Kayden quote.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#Rust command - uses steam api to see if caveman is playing rust, only works if caveman is online
@tree.command(name = "rust", description="see if caveman is playing rust.")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def rust(interaction : discord.Interaction):
    try:
        response = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_key}&steamids=76561198968685475")
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
    except Exception as e:
        print(f"Error in rust command: {e}")
        await on_error(e)
        embed= error_embed("An error occurred while trying to check if Caveman is playing Rust.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
#see what a steam user is playing given a steam id
@tree.command(name = "steamuserplaying", description="Using someones steam id find out if they are playing a game")
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.describe(steamid = "The steam id of the user you want to see")
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def steamUserPlaying(interaction : discord.Interaction, steamid : str):
    try:
        response = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_key}&steamids={steamid}")
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
    except Exception as e:
        print(f"Error in steamUserPlaying command: {e}")
        await on_error(e)
        embed= error_embed("An error occurred while trying to check the user's game. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

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
        if interaction.user.guild_permissions.administrator or  interaction.user.top_role <= user.top_role:
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
        await on_error(e)
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
        if interaction.user.guild_permissions.administrator or  interaction.user.top_role <= user.top_role:
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
        await on_error(e)
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
        await on_error(e)
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
        if interaction.user.guild_permissions.administrator or  interaction.user.top_role <= user.top_role:
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
        await on_error(e)
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
        if interaction.user.guild_permissions.administrator or interaction.user.top_role <= user.top_role:
            await interaction.response.send_message("You cannot remove a warn from a user with a higher or equal role than you.", ephemeral=True)
            return
        try:
            if db.remove_warn(server_warn(server_id=interaction.guild.id, user_id=user.id, count=1)):
                await interaction.response.send_message(f"{user.mention} has had their warn removed for: {reason}")
            else:
                await interaction.response.send_message(f"{user.mention} has no warns to remove.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to remove a warn from this user.", ephemeral=True)
    except Exception as e:
        print(f"Error in remove_warn command: {e}")
        await on_error(e)
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
        await on_error(e)
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
        if amount < 1 or amount > 1000:
            await interaction.response.send_message("You can only purge between 1 and 100 messages.", ephemeral=True)
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
            await interaction.response.send_message("I do not have permission to purge messages in this channel.", ephemeral=True)
    except Exception as e:
        print(f"Error in purge command: {e}")
        await on_error(e)
        embed = error_embed("An error occurred while trying to purge messages. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
#banned words commands

@tree.command(name="addbannedword", description="Add a banned word to the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(word="Word to ban")
async def add_banned_word(interaction : discord.Interaction, word: str):
    try:
        if db.add_banned_word(banned_word(word=word.upper(), server_id=interaction.guild.id)):
            await interaction.response.send_message(f"has been added to the banned words list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"is already banned in this server.", ephemeral=True)
    except Exception as e:
        print(f"Error in add_banned_word: {e}")
        await on_error(e)
        embed = error_embed("An error occurred while trying to add the banned word. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
@tree.command(name="removebannedword", description="Remove a banned word from the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.describe(word="Word to remove from banned words list")
async def remove_banned_word(interaction : discord.Interaction, word: str):
    try:
        if db.remove_banned_word(word=word.upper(), server_id=interaction.guild.id):
            await interaction.response.send_message(f"has been removed from the banned words list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"is not banned in this server.", ephemeral=True)
    except Exception as e:
        print(f"Error in remove_banned_word: {e}")
        await on_error(e)
        embed = error_embed("An error occurred while trying to remove the banned word. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="iswordbanned", description="Check if a word is banned in the server")
@discord.app_commands.allowed_installs(guilds=True, users=False)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@discord.app_commands.describe(word="Word to check if it is banned")
async def is_word_banned(interaction : discord.Interaction, word: str):
    try:
        if db.is_word_banned(word=word.upper(), server_id=interaction.guild.id):
            await interaction.response.send_message(f"is banned in this server.", ephemeral=True)
        else:
            await interaction.response.send_message(f"is not banned in this server.", ephemeral=True)
    except Exception as e:
        print(f"Error in is_word_banned: {e}")
        await on_error(e)
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
        await on_error(e)
        embed = error_embed("An error occurred while trying to remove all banned words. Please try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

#message events

@client.event
async def on_message(message : discord.Message):
    if message.author == client.user:
        return

    if message.author.id == owner:
        if message.content.startswith("!debug"):
            global debug
            debug = not debug
            await message.channel.send(f"Debug mode is now {'on' if debug else 'off'}")
            return
    
    #scan message content
    try:
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
                if db.is_word_banned(attachment.filename, message.guild.id):
                    await message.delete()
                    return
    except Exception as e:
        print(f"Error in on_message: {e}")
        await on_error(e)

client.run(token)