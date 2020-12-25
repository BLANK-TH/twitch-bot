import requests
import json
import traceback
import sys
import praw
import datetime
from random import choice
from twitchio.ext import commands
from twitchio.ext.commands.errors import *
from os import environ, getenv, execv, mkdir
from os.path import isfile, isdir
from pathlib import Path
from dotenv import load_dotenv
from difflib import SequenceMatcher

def graceful_exit(restart=False):
    """Properly exit the program with appropriate exit operations"""
    save_data()
    if restart:
        execv(sys.executable, ["python"] + sys.argv)
    exit()

def assert_data():
    if not isdir("data"):
        mkdir("data")
    if not isfile("data/lists.json"):
        with open("data/lists.json", "w") as f:
            json.dump({"cache": {"restart": False}, "counts": {"goodhuman": 0, "goodbot": 0}, "modlist": [],
                       "sabotagemessages": [], "transcribers": []}, f, indent=2)

def save_data():
    assert_data()
    with open("data/lists.json", "w") as f:
        json.dump(lists, f, indent=2)

def get_gamma() -> int:
    last_comment = reddit.submission(url=osecrets["tor_flair_link"]).comments[0]
    while True:
        if last_comment.id != osecrets["tor_flair_comment_id"]:
            last_comment = last_comment.replies[0]
        else:
            flair_text = last_comment.author_flair_text
            break
    return int(flair_text.split("Γ")[0])

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

async def add_remove_action(ctx, action, value, data_name, appearance_name):
    action = action.lower()
    if action not in ["add", "remove"]:
        await ctx.send("Invalid action \"{}\"".format(action))
        return
    if value is None:
        await ctx.send("No value provided for action \"{}\"".format(action))
        return
    if not ctx.author.is_mod:
        await ctx.send("@{} This command is for mods only".format(ctx.author.name))
        return
    if action == "add":
        if value in lists[data_name]:
            await ctx.send("\"{}\" is already in {} list".format(value, appearance_name))
            return
        lists[data_name].append(value)
    elif action == "remove":
        if value not in lists["sabotagemessages"]:
            await ctx.send("\"{}\" is not in {} list".format(value, appearance_name))
            return
        lists[data_name].remove(value)
    save_data()
    await ctx.send("Successfully {}{} \"{}\" {} {} list".format(action, "d" if action[:-1] == "e" else "ed",
                                                                value, "to" if action == "add" else "from",
                                                                appearance_name))


twitch_secrets = ["IRC_TOKEN", "CLIENT_ID", "NICK", "PREFIX", "INITIAL_CHANNELS"]
reddit_secrets = ["REDDIT_ID", "REDDIT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
other_secrets = ["PI_WEBHOOK", "REMINDERS_WEBHOOK", "TOR_FLAIR_LINK", "TOR_FLAIR_COMMENT_ID"]

envi = True
# Check if secrets are in environment variables
for secret in twitch_secrets + reddit_secrets + other_secrets:
    if secret not in environ.keys():
        envi = False
        break
# If not, check .env file
if not envi:
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)
# Load secrets
secrets = {}
for secret in twitch_secrets:
    if secret != "INITIAL_CHANNELS":
        secrets[secret.lower()] = getenv(secret)
    else:
        secrets[secret.lower()] = [getenv(secret)]
rsecrets = {}
for secret in reddit_secrets:
    rsecrets[secret.lower()] = getenv(secret)
osecrets = {}
for secret in other_secrets:
    osecrets[secret.lower()] = getenv(secret)
# Check all secrets are present
for secret in secrets.values():
    if secret is None:
        print("Cannot get required secret")
        exit()
for secret in rsecrets.values():
    if secret is None:
        print("Cannot get required secret")
        exit()
for secret in osecrets.values():
    if secret is None:
        print("Cannot get other secret")
        exit()

# Load stored data
assert_data()
with open("data/lists.json", "r") as f:
    lists = json.load(f)

# Create bot instance
client = commands.Bot(**secrets)

# Create PRAW instance for reddit commands
reddit = praw.Reddit(user_agent="BLANK_DvTH Twitch Stream Bot", client_id=rsecrets["reddit_id"],
                     client_secret=rsecrets["reddit_secret"], username=rsecrets["reddit_username"],
                     password=rsecrets["reddit_password"])

# Set starting gamma value
if lists["cache"]["restart"]:
    starting_gamma = lists["cache"]["starting_gamma"]
    lists["cache"]["restart"] = False
    save_data()
else:
    starting_gamma = get_gamma()

@client.event
async def event_ready():
    """Called when bot is ready"""
    print("Bot Ready")
    # noinspection PyProtectedMember
    ws = client._ws
    await ws.send_privmsg(secrets["initial_channels"][0], "/me is now online, see my commands with \"{}help\"".format(secrets["prefix"]))

@client.event
async def event_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        command = ctx.message.content[len(secrets["prefix"]):]
        command_similarities = {}
        for cmd in client.commands.keys():
            command_similarities[similar(command,cmd)] = cmd
        if len(command_similarities) == 0:
            await ctx.send("Invalid Command, no similar commands found.")
        highest_command = max([*command_similarities]), command_similarities[max([*command_similarities])]
        if highest_command[0] < 0.55:
            await ctx.send("Invalid Command, no commands with greater than 55% similarity found.")
        else:
            await ctx.send("Invalid Command, did you mean \"{}\"?".format(highest_command[1]))
        return
    if isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing Required Argument: {}. For more info on how to use this command, look at the help "
                       "documentation ({}help)".format(error.param.name, secrets["prefix"]))
        return
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    await ctx.send("{} while executing command {}".format(type(error).__name__, ctx.message.content[len(secrets["prefix"]):]))

@client.event
async def event_message(message):
    """Called when message is sent"""
    # Ignore the bots own messages (wouldn't want infinite loops now do we)
    if message.author.name.lower() == secrets["nick"].lower():
        return
    if secrets["prefix"] != message.content[len(secrets["prefix"]):].lower() and "good bot" in message.content:
        await message.channel.send("Thanks")
    # Handle any commands that might appear
    await client.handle_commands(message)

@client.event
async def event_join(user):
    if user.name.casefold() in lists["modlist"]:
        # noinspection PyProtectedMember
        ws = client._ws
        await ws.send_privmsg(secrets["initial_channels"][0], "Everyone run! @{} is here!".format(user.name))
    elif user.name.casefold() == "cloakknight2":
        # noinspection PyProtectedMember
        ws = client._ws
        await ws.send_privmsg(secrets["initial_channels"][0], "Looks like madlad @{} is here, say byebye to all of "
                                                              "your posts!".format(user.name))

@client.command()
async def test(ctx):
    choices = ["I'm working!", "What is there to test?", "What? You think I'm broken?"]
    await ctx.send(choice(choices))

@client.command(aliases=["pi"])
async def piwarning(ctx):
    requests.post(osecrets["pi_webhook"], data=json.dumps({"content": "<@616032766974361640> {} has warned that the "
                                                                      "current post contains PI!"
                                                          .format(ctx.author.name)}),
                  headers={"Content-Type": "application/json"})
    await ctx.send("BLANK_DvTH has been warned through a discord ping")

@client.command()
async def goodbot(ctx):
    if ctx.author.name.casefold() == "blank_dvth":
        await ctx.send("You can't call yourself a good bot!")
    else:
        lists["counts"]["goodbot"] += 1
        await ctx.send("@BLANK_DvTH has been called a good bot {:,} times. "
                       "They're only half-bot! The human side is doing the streaming, "
                       "better complement the human with \"{}goodhuman\".".format(lists["counts"]["goodbot"], secrets["prefix"]))
        save_data()

@client.command()
async def goodhuman(ctx):
    if ctx.author.name.casefold() == "blank_dvth":
        await ctx.send("You can't call yourself a good human!")
    else:
        lists["counts"]["goodhuman"] += 1
        await ctx.send("@BLANK_DvTH has been called a good human {:,} times.".format(lists["counts"]["goodhuman"]))
        save_data()

@client.command()
async def remindme(ctx, *, reminder):
    if ctx.author.name.casefold() != "blank_dvth":
        await ctx.send("@{} This command is for BLANK only. If there's more demand for this command I may come up with "
                       "a public version that works on a time basis (e.g. {}remindme 1m test).".format(ctx.author.name,
                                                                                                       secrets["prefix"]))
        return
    requests.post(osecrets["reminders_webhook"], data=json.dumps({"content": reminder}),
                  headers={"Content-Type": "application/json"})

@client.command(name="exit")
async def _exit(ctx):
    if ctx.author.name.casefold() != "blank_dvth":
        await ctx.send("@{} This command is for BLANK only".format(ctx.author.name))
        return
    await ctx.send("@{} exiting...".format(ctx.author.name))
    graceful_exit()

@client.command(name="restart")
async def _restart(ctx, cache_data="true"):
    if not ctx.author.is_mod:
        await ctx.send("@{} This command is for mods only".format(ctx.author.name))
        return
    vals = {"true": True, "false": False}
    if cache_data.lower() not in vals.keys():
        await ctx.send("Invalid boolean value for cache_data argument")
        return
    cache_data = vals[cache_data.lower()]
    await ctx.send("@{} restarting...".format(ctx.author.name))
    if cache_data:
        lists["cache"]["restart"] = True
        lists["cache"]["starting_gamma"] = starting_gamma
    graceful_exit(restart=True)

@client.command()
async def progress(ctx):
    gamma = get_gamma()
    await ctx.send("{:,} transcription{} have been done this stream.".format(gamma - starting_gamma,
                                                                             "s" if gamma - starting_gamma != 1 else ""))

@client.command(name="getgamma", aliases=["gamma"])
async def _get_gamma(ctx):
    await ctx.send("BLANK is currently at {:,}Γ".format(get_gamma()))

@client.command(name="startinggamma", aliases=["sg"])
async def _starting_gamma(ctx, new_gamma:int=None):
    global starting_gamma
    if not ctx.author.is_mod:
        await ctx.send("@{} This command is for mods only".format(ctx.author.name))
        return
    if new_gamma is None:
        # noinspection PyUnboundLocalVariable
        await ctx.send("Starting gamma is currently set to {:,}Γ".format(starting_gamma))
    else:
        old_starting = starting_gamma
        starting_gamma = new_gamma
        await ctx.send("Starting gamma has been changed from {:,}Γ to {:,}Γ".format(old_starting, starting_gamma))

@client.command()
async def addmod(ctx, mod):
    if not ctx.author.is_mod:
        await ctx.send("@{} This command is for mods only".format(ctx.author.name))
        return
    lists["modlist"].append(mod)
    save_data()
    await ctx.send("Added mod {} to mod list".format(mod))

@client.command()
async def deletemod(ctx, mod):
    if not ctx.author.is_mod:
        await ctx.send("@{} This command is for mods only".format(ctx.author.name))
        return
    lists["modlist"].remove(mod)
    save_data()
    await ctx.send("Removed mod {} from mod list".format(mod))

@client.command()
async def christmas(ctx):
    date = datetime.datetime.utcnow()
    next_xmas = datetime.datetime(date.year, 12, 25)
    if next_xmas < date:
        next_xmas = datetime.datetime(date.year + 1, 12, 25)
    tdelta = next_xmas - date
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    formatted_time = "{} day{}, {} hour{}, {} minute{}, and {} second{}".format(d["days"],
                                                                                "s" if str(d["days"]) != "1" else "",
                                                                                d["hours"],
                                                                                "s" if str(d["hours"]) != "1" else "",
                                                                                d["minutes"],
                                                                                "s" if str(d["minutes"]) != "1" else "",
                                                                                d["seconds"],
                                                                                "s" if str(d["seconds"]) != "1" else "")
    await ctx.send("{} until Christmas {} in UTC".format(formatted_time, next_xmas.strftime("%Y-%m-%d %H:%M:%S")))

@client.command()
async def sabotage(ctx, action=None, *, value=None):
    if action is not None:
        await add_remove_action(ctx, action, value, "sabotagemessages", "sabotage")
        return
    await ctx.send("@{} has {}.".format(ctx.author.name, choice(lists["sabotagemessages"])))

@client.command()
async def transcribers(ctx, action=None, *, value=None):
    if action is not None:
        await add_remove_action(ctx, action, value, "transcribers", "streaming transcriber")
        return
    await ctx.send("Here's a list of other transcribers that stream: " + ", ".join(["{0} (twitch.tv/{0})".format(t)
                                                                                    for t in lists["transcribers"]]))

@client.command(aliases=["c"])
async def calculate(ctx, *, expression):
    try:
        result = eval(expression,{},{})
        await ctx.send("The answer to \"{}\" is \"{:,}\"".format(expression,result))
    except Exception as e:
        await ctx.send("An error has occurred, please ensure that you entered a valid expression! Error: \"{}\"".format(
            type(e).__name__ + ": " + str(e)))

@client.command(name="8ball")
async def _8ball(ctx, *, question=None):
    if question is None:
        await ctx.send("@{} what are you asking me again?".format(ctx.author.name))
        return
    responses = ["It is certain", "It is decidedly so", "Without a doubt", "Yes definitely", "You may rely on it",
     "As I see it, yes", "Most likely", "Yes", "Signs point to yes", "Reply hazy, try again", "Ask again later",
     "Better not tell you now", "Cannot predict now", "Don't count on it", "My reply is no", "My sources say no",
     "Very doubtful"]
    await ctx.send("@" + ctx.author.name + " " + choice(responses))

@client.command(name="help", aliases=["commands"])
async def _help(ctx):
    await ctx.send("Here's a link to the commands for this bot: "
                   "https://www.github.com/BLANK-TH/twitch-bot/blob/master/commands.md")

client.run()
