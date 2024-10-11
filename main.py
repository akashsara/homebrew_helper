import asyncio
import os
import random
import re
from collections import Counter

import discord
from discord.ext import commands
from discord.ext.commands import Bot, DefaultHelpCommand

import database
from dice import dice
from utils import gen_utils
from utils.ability import Ability
from utils.item import Item
import templates
import error_messages

from utils.player_character import PlayerCharacter
from config import *
from typing import List, Optional, Dict

import logging


class HomebrewHelper(Bot):
    def __init__(
        self, *args, initial_extensions: List[str], character_cache: Dict, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.initial_extensions = initial_extensions
        self.character_cache = character_cache

    async def setup_hook(self) -> None:
        logger.info("Loading extensions.")
        for extension in self.initial_extensions:
            logger.info(f"Loading Extension: {extension}")
            await self.load_extension(extension)


def load_all_characters() -> Dict:
    db = database.connect_to_db(DB_TOKEN)
    character_information = database.load_all_characters(db)
    characters = {}
    for character_id, character_data in character_information.items():
        character = PlayerCharacter()
        character.import_stats(character_data)
        characters[character_id] = character
    return characters


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

# Load and cache character DB
# WARNING: This is not built to scale
logger.info("Loading DnData.")
character_cache = load_all_characters()
# List of cogs we use
initial_extensions = ["cogs.fun"]
# Create help command
help_command = DefaultHelpCommand(no_category="Commands")
# Set intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = HomebrewHelper(
    command_prefix=BOT_PREFIX,
    help_command=help_command,
    intents=intents,
    initial_extensions=initial_extensions,
    character_cache=character_cache,
)


@client.command(
    name="git",
    help="Check out my Github repository! Feel free to contribute!",
    brief="Github repository link.",
)
async def git(context):
    await context.send("https://github.com/akashsara/homebrew_helper")


@client.command(
    name="coin_toss",
    aliases=["cointoss", "toss", "flip", "cointoin"],
    help="Tosses a coin and returns the outcome heards or tails.",
    brief="To toss one or many coin(s).",
)
async def coin_toss(context, *num_tosses):
    num_tosses = "".join(num_tosses)
    num_tosses = 1 if not num_tosses.isdigit() else int(num_tosses)
    if num_tosses > COIN_TOSS_MAX_TOSSES:
        result = [
            f"Yo <@{context.author.id}>,",
            "That's just ridiculous and I ain't doing that.",
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


@client.command(
    name="roll_dice",
    aliases=["roll", "r", "R", "ROLL", "Roll"],
    help="Rolls the dice and returns the outcome.",
    brief="To roll one or many dice(s).",
)
async def roll(context, *roll):
    roll = "".join(roll).lower().replace(" ", "")
    author = context.author
    logger.info(f"Roll: {author.name + '#' + author.discriminator} :: {roll}")
    advantage_or_disadvantage = roll[-1] in ["a", "d"]
    repeat_roll = "r" in roll
    if advantage_or_disadvantage:
        is_advantage = roll[-1] == "a"
        result = dice.roll_wrapper(
            roll[:-1], author.id, "adv_disadv", is_advantage=is_advantage
        )
    elif repeat_roll:
        roll, n_repeats = roll.split("r")
        result = dice.roll_wrapper(roll, author.id, "repeat", n_repeats=n_repeats)
    else:
        result = dice.roll_wrapper(roll, author.id, "normal")
    await context.send(result["message"])


@client.command(
    name="roll_initiative",
    aliases=["initiative", "ri", "RI", "rolli"],
    help="Gets the order in which the players will make their move in battle.",
    brief="To get the roll initiative.",
)
async def roll_initiative(context, npc_count=0, npc_name_template="NPC"):
    # We first ensure that there's no errors with the number/names of NPCs
    server = str(context.guild.id)
    try:
        npc_count = int(npc_count)
    except ValueError:
        await context.send(error_messages.ROLL_INITIATIVE_INVALID_NPCS)
        return
    # We take only up to 30 characters to preserve table formatting.
    npc_name = npc_name_template[:30]
    # We have a hard limit on the number of NPCs we roll for.
    if npc_count > INITIATIVE_MAX_NPCS:
        npc_count = INITIATIVE_MAX_NPCS
        await context.send(
            error_messages.ROLL_INITIATIVE_TOO_MANY_NPCS.format(
                max_npcs=INITIATIVE_MAX_NPCS
            )
        )
    # Include the NPCs in the list of players we roll for.
    players_to_roll_for = {
        f"{npc_name} {i+1}": [False, False] for i in range(npc_count)
    }
    # Store the actual reactions separately for easier management
    player_reactions = {
        f"{npc_name} {i+1}": INITIATIVE_REACTIONS["normal_roll"]
        for i in range(npc_count)
    }

    # Send instruction messages to the channel
    roll_initiative_message = await context.send(templates.ROLL_INITIATIVE_INSTRUCTIONS)

    # Add emoji to the message for people to click on
    for reaction in INITIATIVE_REACTIONS.values():
        await roll_initiative_message.add_reaction(reaction)

    def check(reaction, user):
        return user != client.user

    db = database.connect_to_db(DB_TOKEN)

    try:
        while True:
            reaction, reaction_user = await client.wait_for(
                "reaction_add", timeout=60, check=check
            )
            emoji = str(reaction.emoji)
            user = gen_utils.discord_name_to_id(str(reaction_user.id))
            # Get active character if it exists
            query = {"server": server, "user": user}
            current = database.get_details(query, "users", db).get("active")
            author_id = (
                character_cache[current].get_name()
                if current
                else str(reaction_user.name)
            )
            # Test if user input has already happened
            # if it has, erase the previous input
            # Only if this isn't a stop_roll reaction though
            if (
                author_id in players_to_roll_for
                and emoji != INITIATIVE_REACTIONS["stop_roll"]
            ):
                current_reaction = player_reactions[author_id]
                await roll_initiative_message.remove_reaction(
                    current_reaction, reaction_user
                )
                del players_to_roll_for[author_id]
                del player_reactions[author_id]

            # Identify reaction and track it
            if emoji == INITIATIVE_REACTIONS["normal_roll"]:
                players_to_roll_for[author_id] = [False, False]
                player_reactions[author_id] = INITIATIVE_REACTIONS["normal_roll"]
            elif emoji == INITIATIVE_REACTIONS["advantage_roll"]:
                players_to_roll_for[author_id] = [True, True]
                player_reactions[author_id] = INITIATIVE_REACTIONS["advantage_roll"]
            elif emoji == INITIATIVE_REACTIONS["disadvantage_roll"]:
                players_to_roll_for[author_id] = [True, False]
                player_reactions[author_id] = INITIATIVE_REACTIONS["disadvantage_roll"]
            # Stop if the creator used the stop_roll emoji
            elif (
                emoji == INITIATIVE_REACTIONS["stop_roll"]
                and reaction_user == context.author
            ):
                break
    except asyncio.TimeoutError:
        await context.send(error_messages.ROLL_INITIATIVE_TIMEOUT)

    # Basic check to ensure we actually have players to roll for
    if len(players_to_roll_for) != 0:
        roll_list = []
        # Make rolls for each player and store
        for author_id, (use_advantage, is_advantage) in players_to_roll_for.items():
            if use_advantage:
                outcome = dice.roll_wrapper(
                    "1d20", author_id, "adv_disadv", is_advantage=is_advantage
                )
                player_name = f"{author_id} ({'A' if is_advantage else 'D'})"
            else:
                outcome = dice.roll_wrapper("1d20", author_id, "normal")
                player_name = author_id
            result = {
                "player": player_name,
                "result": outcome["final_result"][0],
                "all_rolls": [str(x["total"]) for x in outcome["raw"]],
            }
            roll_list.append(result)
        # Sort the rolls and prepare output string
        output_string = ""
        for player_roll in sorted(roll_list, key=lambda x: x["result"], reverse=True):
            result = player_roll["result"]
            all_rolls = player_roll["all_rolls"]
            player_name = player_roll["player"]
            # Formatting for the final result
            result = str(result).rjust(2)
            # Formatting for adv/disadv rolls
            if len(all_rolls) == 2:
                all_rolls[0] = all_rolls[0].rjust(2)
                all_rolls[1] = all_rolls[1].rjust(2)
                all_rolls = f"({all_rolls[0]},{all_rolls[1]})"
            # Formatting for normal rolls (no numbers, only spaces)
            else:
                # 2 brackets, a comma, 4 digits
                all_rolls = " " * 7
            # Formatting for player name
            if len(player_name) < 36:
                player_name = player_name.ljust(36)
            elif len(player_name) > 36:
                player_name = player_name[:36]
            output_string += f"\n| {result} {all_rolls}   | {player_name} |"

        await context.send(
            templates.ROLL_INITIATIVE_START_STRING
            + output_string
            + templates.ROLL_INITIATIVE_END_STRING
        )
    else:
        await context.send(error_messages.ROLL_INITIATIVE_NOT_ENOUGH_PLAYERS)


################################################################################
# Functions that use/need a PlayerCharacter
################################################################################


@client.command(
    name="create_character",
    aliases=["create_char", "cc"],
    help="Coming soon.",
    brief="To create a character.",
)
@commands.has_permissions(administrator=True)
async def create_character(context, user, name, level, gold, *stats):
    # Stats = HP, Attack, Defense, Speed, Dexterity, Charisma, Knowledge, Wisdom, Strength, Constitution,
    server = str(context.guild.id)
    user = gen_utils.discord_name_to_id(user)
    if user:
        try:
            uuid = gen_utils.generate_unique_id(set(character_cache.keys()))
            character = PlayerCharacter(user, name, uuid, *stats, level, gold)
        except TypeError:
            logger.info(
                f"{server}: {context.author.id} submitted an invalid set of stats.>"
            )
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
            character_cache[uuid] = character
            # Write character to DB
            db = database.connect_to_db(DB_TOKEN)
            payload = character_cache[uuid].export_stats()
            query = {"character_id": uuid}
            database.set_details(query, payload, "characters", db)
            # Update user information & set as active character
            query = {"server": server, "user": user}
            user_info = database.get_details(query, "users", db)
            user_info["characters"].append(uuid)
            user_info["active"] = uuid
            database.set_details(query, user_info, "users", db)
            logger.info(f"Created Character for {name} ({user})")
            await context.send(f"Your character has been saved!")
        else:
            await context.send(
                f"Well that was useless. Your character has not been saved."
            )
    else:
        logger.info(f"{server}: couldn't find user: {user}")
        await context.send(f"<@{user}> doesn't exist.")


@client.command(name="info", help="Coming soon.", brief="To get character info.")
async def character_info(context, user=None):
    server = str(context.guild.id)
    if user:
        user = gen_utils.discord_name_to_id(user)
    else:
        user = gen_utils.discord_name_to_id(str(context.author.id))
    if user:
        # Get active character
        db = database.connect_to_db(DB_TOKEN)
        query = {"server": server, "user": user}
        current = database.get_details(query, "users", db).get("active")
        if current:
            await context.send(character_cache[current].info())
        else:
            logger.info(f"{server}: couldn't find character ID for {user}")
            await context.send(f"<@{user}> doesn't have any characters yet.")
    else:
        logger.info(f"{server}: couldn't find user: {user}")
        await context.send(f"<@{user}> doesn't exist.")


@client.command(
    name="change_gold",
    aliases=["gold"],
    help="Coming soon.",
    brief="To add or remove gold.",
)
@commands.has_permissions(administrator=True)
async def change_gold(context, user, amount):
    server = str(context.guild.id)
    user = gen_utils.discord_name_to_id(user)
    amount = int(amount)
    if user:
        # Get active character
        db = database.connect_to_db(DB_TOKEN)
        query = {"server": server, "user": user}
        current = database.get_details(query, "users", db).get("active")
        if current:
            status, gold = character_cache[current].change_gold(amount)
            if status:
                # Write changes to DB
                payload = character_cache[current].export_stats()
                query = {"character_id": current}
                database.set_details(query, payload, "characters", db)
                await context.send(
                    f"{character_cache[current].get_name()} (<@{user}>) received {amount} gold. Their new total is {gold} gold."
                )
            else:
                logger.info(
                    f"{server}: User {user} (Character {current}) does not have enough {gold}"
                )
                await context.send(
                    f"{character_cache[current].get_name()} (<@{user}>) doesn't have enough gold for that. They currently have {gold} gold."
                )
        else:
            logger.info(f"{server}: {user} has no characters.")
            await context.send(f"<@{user}> doesn't have any characters")
    else:
        logger.info(f"{server}: couldn't find user: {user}")
        await context.send(f"<@{user}> doesn't exist.")


def transfer_gold_between_players(server, source_user, target_user, amount):
    db = database.connect_to_db(DB_TOKEN)
    query = {"server": server, "user": source_user}
    source = database.get_details(query, "users", db).get("active")
    query = {"server": server, "user": target_user}
    target = database.get_details(query, "users", db).get("active")
    if source and target:
        # Write Changes to Local Copy
        source_status, source_gold = character_cache[source].change_gold(-1 * amount)
        # If a valid transaction
        if source_status:
            target_status, target_gold = character_cache[target].change_gold(amount)
            # Write changes to DB
            payload = character_cache[source].export_stats()
            query = {"character_id": source}
            database.set_details(query, payload, "characters", db)
            payload = character_cache[target].export_stats()
            query = {"character_id": target}
            database.set_details(query, payload, "characters", db)
            return True, {
                "message": "Success",
                "source_gold": source_gold,
                "target_gold": target_gold,
                "source": source,
                "target": target,
            }
        else:
            return False, {
                "message": "NotEnoughGold",
                "source_gold": source_gold,
                "source": source,
                "target": target,
            }
    else:
        return False, {"message": "NoCharacters", "source": source, "target": target}


@client.command(
    name="transfer_gold",
    aliases=["transfer"],
    help="Coming soon.",
    brief="To transfer gold between characters.",
)
async def transfer_gold(context, amount, target):
    server = str(context.guild.id)
    source_user = str(context.author.id)
    target_user = gen_utils.discord_name_to_id(target)
    amount = int(amount)
    status, result = transfer_gold_between_players(
        server, source_user, target_user, amount
    )
    if amount <= 0:
        await context.send(
            f"<@{source_user}>, Nice try. That doesn't work anymore. Punk."
        )
    elif source_user == target_user:
        await context.send(f"<@{source_user}>, I can't believe you've done this.")
    elif target_user:
        if status:
            await context.send(
                f"{character_cache[result['source']].get_name()} (<@{source_user}>) sent {amount} gold. Their new total is {result['source_gold']} gold. {character_cache[result['target']].get_name()} (<@{target_user}>) received {amount} gold. Their new total is {result['target_gold']} gold."
            )
        elif result["message"] == "NotEnoughGold":
            logger.info(
                f"{server}: User {source_user} (Character {character_cache[result['source']].get_name()}) does not have enough {result['source_gold']}"
            )
            await context.send(
                f"{character_cache[result['source']].get_name()} (<@{source_user}>) doesn't have enough gold for that. They currently have {result['source_gold']} gold."
            )
        elif result["message"] == "NoCharacters":
            if not result["source"] and not result["target"]:
                logger.info(
                    f"{server}: Both {source_user} and {target_user} don't have any characters."
                )
                await context.send(f"Neither users have any characters.")
            elif not result["source"]:
                logger.info(f"{server}: {source_user} has no characters.")
                await context.send(f"<@{source_user}> doesn't have any characters")
            elif not result["target"]:
                logger.info(f"{server}: {target_user} has no characters.")
                await context.send(f"<@{target_user}> doesn't have any characters")
    else:
        logger.info(f"{server} couldn't find character ID for {target_user}")
        await context.send(
            f"Either you forgot to enter an amount or <@{target_user}> doesn't exist."
        )


@client.command(
    name="saving_throw",
    aliases=["st"],
    help="Coming soon.",
    brief="To roll a death saving die.",
)
async def saving_throw(context, stat=None, advantage_or_disadvantage=""):
    server = str(context.guild.id)
    user = gen_utils.discord_name_to_id(str(context.author.id))
    if not stat:
        await context.send(
            f"Hey <@{context.author.id}>, to do a saving throw or ability check do `!st <stat> (a|d)` where stat is one of (con, cha, str, dex, kno, wis). You can also add an a or d to signify advantage or disadvantage."
        )
    stat = stat.lower()[:3]
    # Get active character
    db = database.connect_to_db(DB_TOKEN)
    query = {"server": server, "user": user}
    current = database.get_details(query, "users", db).get("active")
    if current and stat in ALLOWED_STATS:
        bonus = character_cache[current].get_stat(stat)
        sign = "+"
        if bonus < 0:
            sign = "-"
            bonus *= -1
        query = f"1d20{sign}{bonus}"
        if advantage_or_disadvantage:
            query += advantage_or_disadvantage[0]
        await context.invoke(client.get_command("roll"), query)
    elif current:
        logger.info(f"{server}: Invalid stat {stat} for character {current}.")
        await context.send(
            f"Hey <@{context.author.id}>, that doesn't seem like a valid stat."
        )
    else:
        logger.info(f"{server} couldn't find character ID for {user}")
        await context.send(
            f"Hey <@{context.author.id}>, it looks like you haven't created any characters yet."
        )


@client.command(
    name="change_stat",
    aliases=["stat_change"],
    help="Coming soon.",
    brief="To modify character stats.",
)
@commands.has_permissions(administrator=True)
async def change_stat(context, user, stat, value):
    server = str(context.guild.id)
    user = gen_utils.discord_name_to_id(user)
    value = int(value)
    stat = stat.lower()[:3]

    if user:
        # Get active character
        db = database.connect_to_db(DB_TOKEN)
        query = {"server": server, "user": user}
        current = database.get_details(query, "users", db).get("active")
        if current and stat in ALLOWED_STATS:
            old_value = character_cache[current].get_stat(stat)
            character_cache[current].set_stat(stat, value)
            character_name = character_cache[current].get_name()
            # Write changes to DB
            payload = character_cache[current].export_stats()
            query = {"character_id": current}
            database.set_details(query, payload, "characters", db)
            await context.send(
                f"Successfully changed the stat for {character_name}(<@{user}>) from {old_value} to {value}!"
            )
        elif current:
            logger.info(f"{server}: Invalid stat {stat} for character {current}.")
            await context.send(
                f"Hey <@{context.author.id}>, that doesn't seem like a valid stat."
            )
        else:
            logger.info(f"{server} couldn't find character ID for {user}")
            await context.send(
                f"Hey <@{context.author.id}>, it looks like that person doesn't have any characters yet."
            )
    else:
        logger.info(f"{server}: couldn't find user: {user}")
        await context.send(f"<@{user}> doesn't exist.")


@client.command(
    name="add_alias",
    aliases=["add_alt", "aa"],
    help="Coming soon.",
    brief="To add nickname.",
)
@commands.has_permissions(administrator=True)
async def add_alias(context, user1, user2):
    server = str(context.guild.id)
    user1 = gen_utils.discord_name_to_id(user1)
    user2 = gen_utils.discord_name_to_id(user2)
    if user1 and user2:
        db = database.connect_to_db(DB_TOKEN)
        # Change Alias
        query = {"alias": user1}
        payload = {"alias": user1, "original": user2}
        database.set_details(query, payload, "aliases", db)
        # Transfer characters
        database.transfer_characters(server, user1, user2, db)
        await context.send(f"<@!{user1}> is now an alias of <@!{user2}>")
    else:
        if user1:
            logger.info(f"{server}: couldn't find user: {user2}")
            await context.send(f"<@{user2}> doesn't exist.")
        else:
            logger.info(f"{server}: couldn't find user: {user2}")
            await context.send(f"<@{user1}> doesn't exist.")


# @client.command(name="create_ability")
# async def create_ability(context):
#     # Have a file containing abilities
#     # Only Admins can make abilities
#     pass

################################################################################
# Housekeeping Functions
################################################################################


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game("with fate."))


@client.event
async def on_command_error(context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        logger.info(f"MissingRequiredArgument: {error}")
        await context.send(
            f"<@{context.author.id}>, doesn't seem like you gave enough information for that command!"
        )
    elif isinstance(error, commands.MissingPermissions):
        logger.info(f"MissingPermissions: {error}")
        await context.send(f"You have no power here, <@{context.author.id}> the Grey.")
    elif isinstance(error, commands.CommandInvokeError):
        logger.info(f"CommandInvokeError: {error}")
        await context.send(
            f"You messed up with the command there, <@{context.author.id}>. Try again."
        )
    elif isinstance(error, commands.CommandNotFound):
        logger.info(f"CommandNotFound: {error}")
        await context.send(f"<@{context.author.id}> that isn't even a command bro.")
    else:
        raise error


if __name__ == "__main__":
    logger.info("Running client..")
    client.run(TOKEN)
