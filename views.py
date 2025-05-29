import discord

def send_target_view(target: discord.User | discord.Member, target_type: str, reason: str, server: discord.Guild):
    embed = discord.Embed(
            title=f"{target_type}",
            description=f"You {target.name} have been {target_type}\nServer: {server.name}\nReason: {reason}",
            color=discord.Color.blue()
        )
    embed.set_thumbnail(url=server.icon.url if server.icon else None)
    
    return target.send(embed=embed)

def send_help_view(help_list : list) -> discord.Embed:
    embed = discord.Embed(
        title="Help",
        description="Here are the commands you can use:",
        color=discord.Color.green()
    )
    
    for command in help_list:
        embed.add_field(name="\u200b", value=command, inline=False)

    return embed

def send_meowjam_view(quote : str) -> discord.Embed:
    embed = discord.Embed(
        title="MeowJam Quote",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="Quote", value=quote, inline=False)
    
    return embed

def send_kayden_view(quote : str) -> discord.Embed:
    embed = discord.Embed(
        title="Kayden Quote",
        color=discord.Color.orange()
    )
    
    embed.add_field(name="Quote", value=quote, inline=False)
    
    return embed