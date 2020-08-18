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
}

client = Bot(command_prefix=BOT_PREFIX)


@client.command(name="coin_toss", aliases=["cointoss", "toss", "flip"])
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
        user = re.findall("\d+", user)[0]
        users[server][user].append(character)
        filename = DATAFILE_NAMES.get("users")
        file_path = os.path.join(DATA_LOCATION, filename)
        gen_utils.save_file(users, file_path)
        logger.info(f"Created Character for {name} ({user})")
        await context.send(f"Your character has been saved!")
    else:
        await context.send(f"Well that was useless. Your character has not been saved.")


@client.command(name="info")
async def character_info(context):
    server = context.guild.id
    user = str(context.author.id)
    characters = users[server][user]
    if characters:
        await context.send(characters[-1].info())
    else:
        logger.info(f"{server} couldn't find character ID: {user}")
        await context.send(
            f"Hey <@{context.author.id}>, it looks like you haven't created any characters yet."
        )


@client.command(name="change_gold", aliases=["cg", "gold"])
@commands.has_permissions(administrator=True)
async def change_gold(context, user, amount):
    server = context.guild.id
    user = re.findall("\d+", user)[0]
    amount = int(amount)
    characters = users[server][user]
    if characters:
        status, gold = characters[-1].change_gold(amount)
        if status:
            await context.send(
                f"<@{context.author.id}> received {amount} gold. Their new total is {gold} gold."
            )
        else:
            await context.send(
                f"<@{context.author.id}> doesn't have enough gold for that. They currently have {gold} gold."
            )
    else:
        await context.send(f"<@{context.author.id}> doesn't have any characters")


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
    else:
        raise error


if __name__ == "__main__":
    logger.info("Loading DnData..")
    users, abilities, items = gen_utils.load_files(DATA_LOCATION, DATAFILE_NAMES)
    logger.info("Booting up client..")
    client.run(TOKEN)
