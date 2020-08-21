import os
import random
import re
from collections import Counter

import discord
from discord.ext import commands
from discord.ext.commands import Bot

from dice import roll_dice
from utils import gen_utils
from utils.ability import Ability
from utils.item import Item
from utils.logging_util import logger
from utils.player_character import PlayerCharacter

TOKEN = os.environ.get("HOMEBREW_HELPER_TOKEN")
BOT_PREFIX = ("?", "!")
DATA_LOCATION = "data/"
DATAFILE_NAMES = {
    "users": "users.joblib",
    "abilities": "abilities.joblib",
    "items": "items.joblib",
    "characters": "characters.joblib",
    "aliases": "aliases.joblib",
}
ALLOWED_STATS = ["dex", "con", "cha", "kno", "wis", "str"]

client = Bot(command_prefix=BOT_PREFIX)


def get_file_path(filename):
    filename = DATAFILE_NAMES.get(filename)
    return os.path.join(DATA_LOCATION, filename)


def get_user_id(user):
    user = re.findall("\d+", user)[0]
    while user in aliases:
        user = aliases.get(user)
    return str(user)


@client.command(name="coin_toss", aliases=["cointoss", "toss", "flip", "cointoin"])
async def coin_toss(context, *num_tosses):
    num_tosses = "".join(num_tosses)
    num_tosses = 1 if not num_tosses.isdigit() else int(num_tosses)
    if num_tosses > 20:
        result = [
            f"Heya <@{context.author.id}>,",
            "That's just ridiculous and I refuse to do that.",
        ]
    else:
        tosses = random.choices(population=[True, False], k=num_tosses)
        counts = Counter(tosses)
        result = (
            [
                f"Heya <@{context.author.id}>,",
                f"You tossed the coin {num_tosses} time(s)! You got:",
                f"```diff",
            ]
            + ["+ Heads" if toss else "- Tails" for toss in tosses]
            + [f"```Heads: {counts[True]}", f"Tails: {counts[False]}"]
        )
    await context.send("\n".join(result))


@client.command(name="roll_dice", aliases=["roll", "r", "R", "ROLL", "Roll"])
async def roll(context, *roll):
    roll = "".join(roll).lower().replace(" ", "")
    author = context.author
    logger.info(f"Roll: {author.name + '#' + author.discriminator} :: {roll}")
    advantage_or_disadvantage = roll[-1] in ["a", "d"]
    repeat_roll = len(roll.split("r")) > 1
    if advantage_or_disadvantage:
        result = roll_dice.with_advantage_or_disadvantage(
            roll[:-1], roll[-1], author.id
        )
    elif repeat_roll:
        roll, repeats = roll.split("r")
        if repeats.isdigit():
            result = roll_dice.and_repeat(roll, int(repeats), author.id)
        else:
            result = f"<@{author.id}>, if you want to roll multiple times, do`?r <roll>r<num_times>`."
    else:
        result = roll_dice.normally(roll, author.id)
    await context.send(result)


@client.command(name="bungee_gum", aliases=["bg", "bungee", "gum", "bungeegum"])
async def bungee_gum(context):
    await context.send(
        f"<@{context.author.id}>, bungee gum possesses the properties of both rubber and gum."
    )


################################################################################
# Functions that use/need a PlayerCharacter
################################################################################


@client.command(name="create_character", aliases=["create_char", "cc"])
@commands.has_permissions(administrator=True)
async def create_character(context, user, name, level, gold, *stats):
    # Stats = HP, Attack, Defense, Speed, Dexterity, Charisma, Knowledge, Wisdom, Strength, Constitution,
    try:
        character = PlayerCharacter(user, name, *stats, level, gold)
    except TypeError:
        await context.send(
            f"Hey uh <@{context.author.id}>, you're missing some stats there."
        )
        return
    await context.send(
        f"Got it! Your character has now been created. Check it out! If it looks good, send a Y to confirm. Otherwise send a N."
    )
    await context.send(character.info())
    message = await client.wait_for("message", timeout=20)
    if message and message.content.lower()[0] == "y":
        server = context.guild.id
        user = get_user_id(user)
        uuid = gen_utils.generate_unique_id(set(characters.keys()))
        characters[uuid] = character
        users[server][user]["characters"].append(uuid)
        users[server][user]["active"] = uuid
        gen_utils.save_file(users, get_file_path("users"))
        gen_utils.save_file(characters, get_file_path("characters"))
        logger.info(f"Created Character for {name} ({user})")
        await context.send(f"Your character has been saved!")
    else:
        await context.send(f"Well that was useless. Your character has not been saved.")


@client.command(name="info")
async def character_info(context, user=None):
    server = context.guild.id
    if user:
        user = get_user_id(user)
    else:
        user = get_user_id(str(context.author.id))
    current = users[server][user].get("active")
    if current:
        await context.send(characters[current].info())
    else:
        logger.info(f"{server}: couldn't find character ID for {user}")
        await context.send(
            f"<@{context.author.id}> doesn't have any characters yet."
        )


@client.command(name="change_gold", aliases=["gold"])
@commands.has_permissions(administrator=True)
async def change_gold(context, user, amount):
    server = context.guild.id
    user = get_user_id(user)
    amount = int(amount)
    current = users[server][user].get("active")
    if current:
        status, gold = characters[current].change_gold(amount)
        if status:
            gen_utils.save_file(characters, get_file_path("characters"))
            await context.send(
                f"{characters[current].get_name()} (<@{user}>) received {amount} gold. Their new total is {gold} gold."
            )
        else:
            await context.send(
                f"{characters[current].get_name()} (<@{user}>) doesn't have enough gold for that. They currently have {gold} gold."
            )
    else:
        await context.send(f"<@{user}> doesn't have any characters")


@client.command(name="add_alias", aliases=["add_alt", "aa"])
@commands.has_permissions(administrator=True)
async def add_alias(context, user1, user2):
    server = context.guild.id
    user1 = get_user_id(user1)
    user2 = get_user_id(user2)
    if user2 not in aliases:
        aliases[user2] = user1
        users[server][user1]["characters"].extend(users[server][user2]["characters"])
        users[server][user2]["characters"] = []
        gen_utils.save_file(users, get_file_path("users"))
        gen_utils.save_file(aliases, get_file_path("aliases"))
        await context.send(f"<@{user2}> is now an alias of <@{user1}>")
    else:
        await context.send(
            f"<@{user2}> is already an alias of <@{aliases.get(user2)}>."
        )


@client.command(name="saving_throw", aliases=["st"])
async def saving_throw(context, stat=None, advantage_or_disadvantage=""):
    server = context.guild.id
    user = get_user_id(str(context.author.id))
    if not stat:
        await context.send(
            f"Hey <@{context.author.id}>, to do a saving throw or ability check do `!st <stat> (a|d)` where stat is one of (con, cha, str, dex, kno, wis). You can also add an a or d to signify advantage or disadvantage."
        )
    stat = stat.lower()[:3]
    current = users[server][user].get("active")
    if current and stat in ALLOWED_STATS:
        bonus = characters[current].get_stat(stat)
        sign = "+" 
        if bonus < 0: 
            sign = "-"
            bonus *= -1
        query = f"1d20{sign}{bonus}"
        if advantage_or_disadvantage:
            query += advantage_or_disadvantage[0]
        await context.invoke(client.get_command("roll"), query)
    elif current:
        await context.send(
            f"Hey <@{context.author.id}>, that doesn't seem like a valid stat."
        )
    else:
        logger.info(f"{server} couldn't find character ID for {user}")
        await context.send(
            f"Hey <@{context.author.id}>, it looks like you haven't created any characters yet."
        )


# @client.command(name="create_ability")
# async def create_ability(context):
#     # Have a file containing abilities
#     # Only Admins can make abilities
#     pass


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game("with fate."))


@client.event
async def on_command_error(context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await context.send(
            f"<@{context.author.id}>, doesn't seem like you gave enough information for that command!"
        )
    elif isinstance(error, commands.MissingPermissions):
        await context.send(
            f"You have no power here, <@{context.author.id}> the Grey."
        )
    else:
        raise error


if __name__ == "__main__":
    logger.info("Loading DnData..")
    users, characters, abilities, items, aliases = gen_utils.load_files(
        DATA_LOCATION, DATAFILE_NAMES
    )
    logger.info("Booting up client..")
    client.run(TOKEN)
