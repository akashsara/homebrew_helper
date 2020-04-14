import os
import re
import discord
import random
import pickle
from discord.ext.commands import Bot
from player_character import PlayerCharacter
from ability import Ability
from item import Item
import dice

TOKEN = os.environ.get("HOMEBREW_HELPER_TOKEN")
BOT_PREFIX = ("?",)
DATA_LOCATION = "data/"
client = Bot(command_prefix=BOT_PREFIX)


def save_file(data, type_):
    if type_ == "user":
        filename = "users.p"
    elif type_ == "ability":
        filename = "abilities.p"
    elif type_ == "item":
        filename = "items.p"
    with open(f"{DATA_LOCATION}/{filename}", "wb") as fp:
        pickle.dump(data, fp)


@client.command(name="roll_dice", aliases=["roll", "r", "R", "ROLL", "Roll"])
async def roll_dice(context, *roll):
    roll = "".join(roll)
    roll = roll.replace(" ", "")
    author = context.author
    print("Roll:", author, roll)
    roll = dice.roll(roll)
    if roll == "too high":
        await context.send(f"I'm not rolling that absurd number <@{author.id}>.")
    elif roll == "wrong":
        await context.send(f"That's not how you do it <@{author.id}>. Your roll should be of the format XDN or XDN+-Y. X = Number of dice, N = Size of die, Y = Modifier.")
    else:
        await context.send(f"<@{author.id}>'s Roll:\n```fix\nYou rolled a {roll[0]}.\nYou got: {', '.join(str(x) for x in roll[1])}\nYour modifier is: {str(roll[2])}```Your total roll is: **{roll[3]}**")


@client.command(name="create_character", aliases=["create_char", "cc"])
async def create_character(context):
    user = context.author.id
    await context.send(
        f"Hiya <@{user}>, let's make your character!\nWhat is your character called?"
    )
    message = await client.wait_for("message", timeout=120)
    name = message.content
    await context.send(
        f"I see, so your character is called {message.content}.\nNow, enter your stats in the following order (space separated):\n<HP> <Attack> <Defense> <Speed> <Dexterity> <Charisma> <Knowledge> <Wisdom>"
    )
    message = await client.wait_for("message", timeout=120)
    stats = message.content
    gold = 0
    level = 2
    character = PlayerCharacter(user, name, *stats.split(" "), level, gold)
    await context.send(
        f"Got it! Your character has now been created. Check it out!\n{character.short_info()}Does that look alright?\nSend Y to confirm, N to reject."
    )
    message = await client.wait_for("message", timeout=120)
    if message.content.lower()[0] == "y":
        users[user] = character
        save_file(users, "user")
        await context.send(f"Your character has been saved!")
    else:
        await context.send(f"Well that was useless. Your character has not been saved.")


@client.command(name="character_info", aliases=["ci", "info"])
async def character_info(context):
    user = context.author.id
    if user in users:
        character = users[user]
        await context.send(character.short_info())
        await context.send(character.rest_of_the_owl())
    else:
        await context.send(
            f"Sorry <@{user}>, couldn't find a character linked to you. :/"
        )


@client.command(name="create_ability")
async def create_ability(context):
    # Have a file containing abilities
    # Only Admins can make abilities
    pass


if __name__ == "__main__":
    print("Loading DnData..")
    if os.path.isfile("data/users.p"):
        with open("data/users.p", "rb") as fp:
            users = pickle.load(fp)
    else:
        users = dict()
    print("Booting up client..")
    client.run(TOKEN)
