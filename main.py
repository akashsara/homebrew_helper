import os
import pickle
import random
import re

import discord
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
DATAFILE_NAMES = {"user": "users.p", "ability": "abilities.p", "item": "items.p"}

client = Bot(command_prefix=BOT_PREFIX)

@client.command(name="coin_toss", aliases=["cointoss", "toss", "flip"])
async def coin_toss(context, *num_tosses):
    num_tosses = "".join(num_tosses)
    num_tosses = 1 if not num_tosses.isdigit() else int(num_tosses)
    tosses = random.choices(population=[True, False], k=num_tosses)
    result = (
        [f"You tossed the coin {num_tosses} time(s)! You got:", f"```diff"]
        + ["+ Heads" if toss else "- Tails" for toss in tosses]
        + ["```"]
    )
    await context.send('\n'.join(result))


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


# @client.command(name="create_character", aliases=["create_char", "cc"])
# async def create_character(context):
#     user = context.author.id
#     await context.send(
#         f"Hiya <@{user}>, let's make your character!\nWhat is your character called?"
#     )
#     message = await client.wait_for("message", timeout=120)
#     name = message.content
#     await context.send(
#         f"I see, so your character is called {message.content}.\nNow, enter your stats in the following order (space separated):\n<HP> <Attack> <Defense> <Speed> <Dexterity> <Charisma> <Knowledge> <Wisdom>"
#     )
#     message = await client.wait_for("message", timeout=120)
#     stats = message.content
#     gold = 0
#     level = 2
#     character = PlayerCharacter(user, name, *stats.split(" "), level, gold)
#     await context.send(
#         f"Got it! Your character has now been created. Check it out!\n{character.short_info()}Does that look alright?\nSend Y to confirm, N to reject."
#     )
#     message = await client.wait_for("message", timeout=120)
#     if message.content.lower()[0] == "y":
#         users[user] = character
#         filename = DATAFILE_NAMES.get('user')
#         file_path = os.path.join(DATA_LOCATION, filename)
#         save_file(users, file_path)
#         await context.send(f"Your character has been saved!")
#     else:
#         await context.send(f"Well that was useless. Your character has not been saved.")


# @client.command(name="character_info", aliases=["ci", "info"])
# async def character_info(context):
#     user = context.author.id
#     if user in users:
#         character = users[user]
#         await context.send(character.short_info())
#         await context.send(character.rest_of_the_owl())
#     else:
#         await context.send(
#             f"Sorry <@{user}>, couldn't find a character linked to you. :/"
#         )


# @client.command(name="create_ability")
# async def create_ability(context):
#     # Have a file containing abilities
#     # Only Admins can make abilities
#     pass


if __name__ == "__main__":
    logger.info("Loading DnData..")
    users, abilities, items = gen_utils.load_files(DATA_LOCATION, DATAFILE_NAMES)
    logger.info("Booting up client..")
    client.run(TOKEN)
