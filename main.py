import os
import re
import discord
import random
import pickle
from discord.ext.commands import Bot
from utils import dice
from utils.player_character import PlayerCharacter
from utils.ability import Ability
from utils.item import Item
from utils.logging_util import logger

TOKEN = os.environ.get("HOMEBREW_HELPER_TOKEN")
BOT_PREFIX = ("?", "!")
DATA_LOCATION = "data/"
client = Bot(command_prefix=BOT_PREFIX)

too_high = "One or more of your rolls are absurdly high. I'm not rolling that <@{author_id}>."
wrong = "That's not how you do it <@{author_id}>. Your roll should be of the format (roll)(operation)(modifier)(special), where rolls should be of the format XdN (X = Number of Dice; N = Number of Die Faces). Operation is either + or - and modifier is your modifier. Special indicates advantage or disadvantage. Just append your roll with an a or d. Examples: `?r 1d20+2` or `?r 1d20+1d4-2` or `?r 1d20a`."


def save_file(data, type_):
    if type_ == "user":
        filename = "users.p"
    elif type_ == "ability":
        filename = "abilities.p"
    elif type_ == "item":
        filename = "items.p"
    with open(f"{DATA_LOCATION}/{filename}", "wb") as fp:
        pickle.dump(data, fp)

def load_files():
    dicts = [{}, {}, {}]
    for i, filename in enumerate(["users.p", "abilities.p", "items.p"]):
        file_path = os.path.join(f"{DATA_LOCATION}/{filename}")
        if os.path.exists(file_path):
            with open(file_path, "rb") as fp:
                dicts[i] = pickle.load(fp)
    return dicts


def pad(text_to_pad, length_to_pad_to, direction):
    if direction == "left":
        return (" " * (length_to_pad_to - len(text_to_pad))) + text_to_pad
    return text_to_pad + (" " * (length_to_pad_to - len(text_to_pad)))


def format_rolls(rolls):
    new_roll = []
    for item in rolls:
        key, value = item
        num_dice, die_size = key.split("d")
        num_dice = pad(num_dice, 2, "left")
        die_size = pad(die_size, 3, "right")
        total = pad(str(sum(value)), 5, "left")
        new_roll.append(f"{num_dice}d{die_size}: {total} :: {value}")
    return "\n".join(new_roll)

def format_repeated_rolls(rolls):
    full_text = []
    ending = []
    for item in rolls:
        roll = item['user_roll']
        all_in_one = []
        for _, y in item['rolls']:
            all_in_one.extend(y)
        modifier = pad(str(item['modifier']), 2, "left")
        total = pad(str(item['total']), 5, "left")
        ending.append(item['total'])
        full_text.append(f"{roll} : {total} :: {modifier} + {all_in_one}")
    ending = f"Final Rolls: **{ending}**"
    return full_text, ending

@client.command(name="roll_dice", aliases=["roll", "r", "R", "ROLL", "Roll"])
async def roll_dice(context, *roll):
    roll = "".join(roll).lower().replace(" ", "")
    author = context.author
    logger.info(f"Roll: {author.name + '#' + author.discriminator} :: {roll}")
    advantage_or_disadvantage = roll[-1] in ["a", "d"]
    repeat_roll = len(roll.split('r')) > 1
    if advantage_or_disadvantage:
        result = roll_with_advantage_or_disadvantage(
            roll[:-1], roll[-1], author.id
        )
    elif repeat_roll:
        roll, repeats = roll.split('r')
        if repeats.isdigit():
            result = roll_and_repeat(roll, int(repeats), author.id)
        else:
            result = f"<@{author.id}>, if you want to roll multiple times, do`?r <roll>r<num_times>`."
    else:
        result = roll_normally(roll, author.id)
    await context.send(result)


def roll_normally(roll, author_id):
    roll = dice.roll(roll)
    if roll == "too high":
        return too_high.format(author_id=author_id)
    elif roll == "wrong":
        return wrong.format(author_id=author_id)
    else:
        return f"<@{author_id}>'s Roll:\n```fix\nYou rolled a {roll['user_roll']}.\nYou got: \n{format_rolls(roll['rolls'])}\nYour modifier is: {str(roll['modifier'])}```Your total roll is: **{str(roll['total'])}**"


def roll_with_advantage_or_disadvantage(roll, advantage_or_disadvantage, author_id):
    first_roll = dice.roll(roll)
    # Cover these cases in the 1st roll since we'll get the same for the 2nd
    if first_roll == "too high":
        return too_high.format(author_id=author_id)
    elif first_roll == "wrong":
        return wrong.format(author_id=author_id)
    second_roll = dice.roll(roll)
    base_string = f"<@{author_id}>:\n Attempt 1:\n```fix\nYou rolled a {first_roll['user_roll']}.\nYou got: \n{format_rolls(first_roll['rolls'])}\nYour modifier is: {str(first_roll['modifier'])}\nYour total roll is: {str(first_roll['total'])}```Attempt 2:\n```fix\nYou rolled a {second_roll['user_roll']}.\nYou got: \n{format_rolls(second_roll['rolls'])}\nYour modifier is: {str(second_roll['modifier'])}\nYour total roll is: {str(second_roll['total'])}```"
    if advantage_or_disadvantage == "a":
        return base_string + f"Your final roll is: **{max(first_roll['total'], second_roll['total'])}**."
    else:
        return base_string + f"Your final roll is: **{min(first_roll['total'], second_roll['total'])}**."


def roll_and_repeat(roll, num_repeats, author_id):
    first_roll = dice.roll(roll)
    # Cover these cases in the 1st roll since we'll get the same for the 2nd
    if first_roll == "too high":
        return too_high.format(author_id=author_id)
    elif first_roll == "wrong":
        return wrong.format(author_id=author_id)
    list_of_rolls = [first_roll]
    for _ in range(num_repeats - 1):
        list_of_rolls.append(dice.roll(roll))
    main_rolls, ending = format_repeated_rolls(list_of_rolls)
    outputs = [f"<@{author_id}>'s Roll:", "```fix", f"You rolled {roll}."] + main_rolls + ["```" + ending]
    return "\n".join(outputs)

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
#         save_file(users, "user")
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
    users, abilities, items = load_files()
    logger.info("Booting up client..")
    client.run(TOKEN)
