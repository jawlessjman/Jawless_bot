help = """
- /help : will display this help menu
- /hello : makes the bot say hello
- /say : make the bot say a message
- /meowjam : send a meowjam quote
- /kayden : send a kayden quote
- /rust : see if caveman is playing rust
- /steamuserplaying : see what a steam user is playing
- /kick : kick a user from a server
- /ban : ban a user from a server
- /unban : unban a user from a server
- /warn : warn a user in a server
- /removewarn : remove a warn from a user
- /purge : mass delete up to 1000 messages
- /addbannedword : add a word to the server ban list
- /removebannedword : remove a word from the servers ban list
- /iswordbanned : see if a word is banned in the server
- /removeallbannedwords : remove all banned words in a server 
- /set_mute_settings : set the mute role and channel for the server
- /remove_mute_settings : remove the mute role and channel settings for the server
- /mute_user : mute a user in the server
- /unmute_user : unmute a user in the server
"""

kayden_quotes = """
Kayden is typing
You are a man of culture
I don't play gmod anymore
You looking like some roblox user from 2010
Sit you a a braindead loser
"""

meowjam_quotes = """
Take your gummer outside oh your brine
because the world doesn't not evolve around you
asuna your trach
you pull more retarded stuff for judgeing people's english
Are you f** kidding me do you think i'm dumb no i'm not i'm not just going to buy a new headset in wish.xom scammed someone before
Oh am i retarded? what about you're retarded for not having a suitable life you only have online friends you only have one friend that you met on in
So what i can literally go outside and talk to someone and he won't juge about my english because he's not asshole like you guys
because i can literally go out of school and i can seriously speak englush good enough than you can
because you're the only people who gets in people's business and juge about their english
that wasnt a funny jone
Im not frigging no clipping
"""

#convert string into list of help commands
def get_help_text(text : str) -> list:
    return [line.strip() for line in text.strip().split('\n') if line.strip()]

__all__ = ("help_list", "kayden_quote_list", "meowjam_quote_list", "get_help_text")
help_list = get_help_text(help)
kayden_quote_list = get_help_text(kayden_quotes)
meowjam_quote_list = get_help_text(meowjam_quotes)