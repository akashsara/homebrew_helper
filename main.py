import asyncio
import os
import random
import re
from collections import Counter

import discord
from discord.ext import commands
from discord.ext.commands import Bot

import database
from dice import dice, roll_dice
from utils import gen_utils
from utils.ability import Ability
from utils.item import Item
from utils.logging_util import logger
from utils.player_character import PlayerCharacter
from config import *

client = Bot(command_prefix=BOT_PREFIX)


@client.command(name="coin_toss", aliases=["cointoss", "toss", "flip", "cointoin"])
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


@client.command(name="roll_initiative", aliases=["initiative", "ri", "RI", "rolli"])
async def roll_initiative(context, npc_count=None, npc_name_template=None):
    roll_initiative_message = await context.send(
        f"React with,\n👍 to add to the initiative order (or)\n🎖️ to add to the initiative order with advantage (or)\n🚫 to add to the initiative order with disadvantage (or)\n 🛑 to start rolling"
    )
    await roll_initiative_message.add_reaction("👍")
    await roll_initiative_message.add_reaction("🎖️")
    await roll_initiative_message.add_reaction("🚫")
    await roll_initiative_message.add_reaction("🛑")

    def check(reaction, user):
        return user != client.user

    count = 0
    players_to_roll_for = list()
    server = str(context.guild.id)
    if npc_count:
        npc_character_count = int(npc_count)
        npc_character_name = "NPC"
        if npc_name_template:
            npc_character_name = npc_name_template
            if len(npc_character_name) > 29:
                npc_character_name = npc_character_name[:30]
        if npc_character_count > INITIATIVE_MAX_NPCS:
            npc_character_count = INITIATIVE_MAX_NPCS
            await context.send(
                f"Um...if you have more than {INITIATIVE_MAX_NPCS} NPCs in combat, please don't. I'm considering only {INITIATIVE_MAX_NPCS}."
            )
        for i in range(npc_character_count):
            players_to_roll_for.append([f"{npc_character_name} {i+1}", ""])

    db = database.connect_to_db(DB_TOKEN)
    while count < 2:
        try:
            reaction, reaction_user = await client.wait_for(
                "reaction_add", timeout=60, check=check
            )
            user = gen_utils.discord_name_to_id(str(reaction_user.id))
            # Get active character
            query = {"server": server, "user": user}
            current = database.get_details(query, "users", db).get("active")
            if current:
                display_name = character_cache[current].get_name()
            else:
                display_name = str(reaction_user.name)
            multi_input_flag = False
            for items in players_to_roll_for:
                if items[0] == display_name:
                    multi_input_flag = True
            if str(reaction.emoji) == "👍" and not multi_input_flag:
                players_to_roll_for.append([display_name, ""])
            elif str(reaction.emoji) == "🎖️" and not multi_input_flag:
                players_to_roll_for.append([display_name, "a"])
            elif str(reaction.emoji) == "🚫" and not multi_input_flag:
                players_to_roll_for.append([display_name, "d"])
            elif str(reaction.emoji) == "🛑":
                if reaction_user == context.author:
                    count = 10
                else:
                    await context.send(
                        f"Only <@{context.author.id}> can start the roll"
                    )
        except asyncio.TimeoutError:
            await context.send(f"Look, a minute's gone by and I'm not waiting anymore.")

    if len(players_to_roll_for) != 0:
        roll_list = []
        display_output = "Roll Order:\n```\n+--------------+--------------------------------------+\n| Roll         | Player Name                          |\n+--------------+--------------------------------------+"
        for x in players_to_roll_for:
            if x[1] == "":
                result = {"player": x[0], "roll": dice.roll("1d20")["total"], "outcome": None}
            else:
                outcome = roll_dice.with_advantage_or_disadvantage("1d20", x[1], x[0], raw_flag=True)
                result = {"player": x[0]+" ("+x[1].upper()+")", "roll": outcome[0], "outcome": outcome[1]}
            roll_list.append(result)
        for player_roll in sorted(roll_list, key=lambda x: x["roll"], reverse=True):
            roll = player_roll["roll"]
            outcome = player_roll["outcome"]
            player_name = player_roll["player"]
            if len(str(roll)) == 1:
                roll = f" {roll}"
            if type(outcome) == list and len(str(outcome[0])) == 1:
                outcome[0] = f" {outcome[0]}"
            if type(outcome) == list and len(str(outcome[1])) == 1:
                outcome[1] = f" {outcome[1]}"
            if len(player_name) < 36:
                for i in range(36 - len(player_name)):
                    player_name += " "
            if len(player_name) > 36:
                player_name = player_name[:36]
            if type(outcome) == list:
                outcome = f"({outcome[0]},{outcome[1]})"
            else:
                outcome = "       "
            display_output += f"\n| {roll} {outcome}   | {player_name} |"
        await context.send(
            display_output + "\n+--------------+--------------------------------------+```"
        )
    else:
        await context.send("Thank you for wasting my time :)")


################################################################################
# Fun Commands - No Dependencies
################################################################################


@client.command(name="bungee_gum", aliases=["bg", "bungee", "gum", "bungeegum"])
async def bungee_gum(context):
    await context.send(
        f"<@{context.author.id}>, bungee gum possesses the properties of both rubber and gum."
    )


@client.command(name="cow", aliases=["moo"])
async def cow(context):
    await context.send(f"MOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.")


@client.command(name="rick", aliases=["rickroll"])
async def rickroll(context):
    selection = random.choice(RICK_ROLL_LYRICS)
    await context.send("```" + "\n".join(selection) + "```")


@client.command(name="fighting_words", aliases=["insult", "banter", "trash_talk"])
async def fighting_words(context):
    selection = random.choice(FIGHTING_WORDS)
    await context.send(selection)


@client.command(name="wise_words", aliases=["wise", "wisdom"])
async def wise_words(context):
    quote = random.choice(WISE_QUOTES)
    await context.send(quote)


@client.command(name="oracle")
async def oracle(context):
    author = f"<@{context.author.id}>"
    message = context.message.content[8:]
    await context.send(f"{author}: {message}\nAnswer: {random.choice(ORACLE_ANSWERS)}")


@client.command(name="report", aliases=["report_lan"])
async def report(context):
    author = f"<@{context.author.id}>"
    message = await context.send(f"{author}: Please wait...preparing report.")
    await asyncio.sleep(2)
    await message.edit(content="Report Prepared.")
    await asyncio.sleep(2)
    if random.randint(0, 100) == 69:
        await message.edit(
            content=f"Thank you for reporting {random.choice(REPORTABLE_PEOPLE)}, {author}!"
        )
    else:
        await message.edit(
            content=f"Thank you for reporting {ALWAYS_REPORT}, {author}!"
        )


################################################################################
# Functions that use/need a PlayerCharacter
################################################################################


@client.command(name="create_character", aliases=["create_char", "cc"])
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


@client.command(name="info")
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


@client.command(name="change_gold", aliases=["gold"])
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


@client.command(name="transfer_gold", aliases=["transfer"])
async def transfer_gold(context, amount, target):
    server = str(context.guild.id)
    source_user = str(context.author.id)
    target_user = gen_utils.discord_name_to_id(target)
    amount = int(amount)
    status, result = transfer_gold_between_players(
        server, source_user, target_user, amount
    )
    if target_user:
        if status:
            await context.send(
                f"{character_cache[result['source']].get_name()} (<@{source_user}>) sent {amount} gold. Their new total is {result['source_gold']} gold. {character_cache[result['target']].get_name()} (<@{target_user}>) received {amount} gold. Their new total is {result['target_gold']} gold."
            )
        elif result["message"] == "NotEnoughGold":
            logger.info(
                f"{server}: User {source_user} (Character {result['source'].get_name()}) does not have enough {result['source_gold']}"
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


@client.command(name="saving_throw", aliases=["st"])
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


@client.command(name="change_stat", aliases=["stat_change"])
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


@client.command(name="add_alias", aliases=["add_alt", "aa"])
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
        await context.send(
            f"<@{context.author.id}>, doesn't seem like you gave enough information for that command!"
        )
    elif isinstance(error, commands.MissingPermissions):
        await context.send(f"You have no power here, <@{context.author.id}> the Grey.")
    else:
        raise error


def load_all_characters():
    db = database.connect_to_db(DB_TOKEN)
    character_information = database.load_all_characters(db)
    characters = {}
    for character_id, character_data in character_information.items():
        character = PlayerCharacter()
        character.import_stats(character_data)
        characters[character_id] = character
    return characters


if __name__ == "__main__":
    logger.info("Loading DnData..")
    character_cache = load_all_characters()
    logger.info("Booting up client..")
    client.run(TOKEN)
