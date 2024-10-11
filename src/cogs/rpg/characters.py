import json
import logging

import src.config as config
from discord.ext import commands
from pymongo import MongoClient
from src.templates import *
from src.utils import database, gen_utils, player_character


# Ref: https://stackoverflow.com/questions/65595213/how-to-add-shared-cooldown-to-multiple-discord-py-commands
class RPGCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("bot.rpg_commands")

    @commands.command(
        name="create_character",
        aliases=["create_char", "cc"],
        help="Coming soon.",
        brief="To create a character.",
    )
    @commands.has_permissions(administrator=True)
    async def create_character(self, context, user, *character_info):
        """
        character_info is a dictionary with the following keys:
            name: name of the character
            hp: maximum health / hit points
            attack: attack stat / attack bonus
            armor_class: defense stat / to-hit
            speed: movement speed
            level: level of the character
            gold: amount of gold or other currency the character possesses
            stats: dictionary of stat_name:stat_value for all stats.
                May contain a nested dictionary.
        """
        server = str(context.guild.id)
        user_id = gen_utils.discord_name_to_id(user)
        character_info = "".join(character_info)
        # Invalid or no user
        if user_id:
            # Heuristic that ensures mimimum info is present
            if len(character_info) > 50:
                # Load character info if possible
                try:
                    character_info = json.loads(character_info)
                    # Validate character info
                    result = player_character.validate_character(character_info)
                    if result["status"]:
                        # Create character
                        uuid = gen_utils.generate_unique_id(
                            set(self.bot.character_cache.keys())
                        )
                        character = player_character.PlayerCharacter(
                            user_id, uuid, character_info
                        )
                        await context.send(CREATE_CHARACTER_CONFIRM_PROMPT)
                        await context.send(character.info())
                        try:
                            message = await self.bot.wait_for("message", timeout=60)
                            if message and message.content.lower()[0] == "y":
                                # Write character to DB
                                with MongoClient(config.DB_TOKEN) as db:
                                    db = db[config.DB_NAME]
                                    payload = character.export_stats()
                                    query = {"character_id": uuid}
                                    database.set_details(
                                        query, payload, "characters", db
                                    )
                                    # Update user information & set as active character
                                    query = {"server": server, "user": user_id}
                                    user_info = database.get_details(query, "users", db)
                                    if user_info:
                                        user_info["characters"].append(uuid)
                                    else:
                                        user_info = {
                                            "server": server,
                                            "user": user_id,
                                            "characters": [uuid],
                                        }
                                    user_info["active"] = uuid
                                    database.set_details(query, user_info, "users", db)
                                # Update local caches
                                self.bot.character_cache[uuid] = character
                                if server not in self.bot.user_cache:
                                    self.bot.user_cache[server] = {}
                                self.bot.user_cache[server][user_id] = user_info
                                await context.send(CREATE_CHARACTER_SUCCESS)
                            else:
                                await context.send(CREATE_CHARACTER_CANCEL)
                        except TimeoutError:
                            await context.send(CREATE_CHARACTER_CANCEL)
                        except Exception as e:
                            self.logger.warning("Failed to create character", e)
                            await context.send("UNKNOWN ERROR! Report & Contact Lan!!")
                    else:
                        await context.send(
                            CREATE_CHARACTER_INVALID_STATS.format(
                                user=context.author.id, error=result["error"]
                            )
                        )
                except json.decoder.JSONDecodeError:
                    await context.send(CREATE_CHARACTER_JSON_ERROR)
            else:
                await context.send(CREATE_CHARACTER_NO_INFO.format(user=user_id))
        else:
            await context.send(USER_NOT_FOUND.format(user=user))

    @commands.command(name="info", help="Coming soon.", brief="To get character info.")
    async def character_info(self, context, user=None):
        if user:
            user_id = gen_utils.discord_name_to_id(user)
        else:
            user_id = gen_utils.discord_name_to_id(str(context.author.id))
        if user_id:
            # Get server ID
            server = str(context.guild.id)
            # Get active character
            current = self.bot.get_current_chara(server, user_id)
            if current:
                await context.send(self.bot.character_cache[current].info())
            else:
                await context.send(CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="saving_throw",
        aliases=["st", "stat_roll"],
        help="Coming soon.",
        brief="To roll a saving throw for your character.",
    )
    async def saving_throw(self, context, stat=None, advantage_or_disadvantage=""):
        server = str(context.guild.id)
        user_id = gen_utils.discord_name_to_id(str(context.author.id))
        if not stat:
            await context.send(
                f"Hey <@{context.author.id}>, to do a saving throw or ability check do `!st <stat> (a|d)`. You can also add an a or d to signify advantage or disadvantage."
            )
        # Get active character
        current = self.bot.get_current_chara(server, user_id)
        if current:
            stat_name = self.bot.character_cache[current].resolve_stat_name(stat)
            if stat_name:
                stat_bonus = self.bot.character_cache[current].get_stat(stat_name)
                sign = "+" if stat_bonus > 0 else ""
                query = f"1d20{sign}{stat_bonus}"
                if advantage_or_disadvantage:
                    query += advantage_or_disadvantage[0]
                if "__" in stat_name:
                    key, subkey = stat_name.split("__")
                    stat_name = key if subkey == "base" else subkey
                await context.send(f"Rolling for {gen_utils.format_stat(stat_name)}.")
                await context.invoke(self.bot.get_command("roll"), query)
            else:
                await context.send(INVALID_STAT.format(user=user_id))
        else:
            await context.send(CHARACTER_NOT_FOUND.format(user=user_id))

    @commands.command(
        name="attack",
        help="Coming soon.",
        brief="To make an attack roll.",
    )
    async def attack(self, context, advantage_or_disadvantage=""):
        server = str(context.guild.id)
        user_id = gen_utils.discord_name_to_id(str(context.author.id))
        # Get active character
        current = self.bot.get_current_chara(server, user_id)
        if current:
            stat_bonus = self.bot.character_cache[current].get_attack()
            sign = "+" if stat_bonus > 0 else ""
            query = f"1d20{sign}{stat_bonus}"
            if advantage_or_disadvantage:
                query += advantage_or_disadvantage[0]
            await context.invoke(self.bot.get_command("roll"), query)
        else:
            await context.send(CHARACTER_NOT_FOUND.format(user=user_id))

    @commands.command(
        name="change_stat",
        aliases=["stat_change"],
        help="Coming soon.",
        brief="To modify character stats.",
    )
    @commands.has_permissions(administrator=True)
    async def change_stat(self, context, user, stat, value):
        server = str(context.guild.id)
        user_id = gen_utils.discord_name_to_id(user)
        value = int(value)
        if user_id:
            # Get active character
            current = self.bot.get_current_chara(server, user_id)
            if current:
                stat_name = self.bot.character_cache[current].resolve_stat_name(stat)
                if stat_name:
                    self.bot.character_cache[current].set_stat(stat_name, value)
                    character_name = self.bot.character_cache[current].get_name()
                    # Write changes to DB
                    payload = self.bot.character_cache[current].export_stats()
                    query = {"character_id": current}
                    with MongoClient(config.DB_TOKEN) as db:
                        database.set_details(
                            query, payload, "characters", db[config.DB_NAME]
                        )
                    await context.send(
                        STAT_CHANGE_SUCCESSFUL.format(
                            character_name=character_name,
                            stat_name=gen_utils.format_stat(stat_name),
                            user=user_id,
                            value=value,
                        )
                    )
                else:
                    await context.send(INVALID_STAT.format(user=user_id))
            else:
                await context.send(CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="add_alias",
        aliases=["add_alt", "aa"],
        help="Coming soon.",
        brief="To add nickname.",
    )
    @commands.has_permissions(administrator=True)
    async def add_alias(self, context, user1, user2):
        server = str(context.guild.id)
        user1_id = gen_utils.discord_name_to_id(user1)
        user2_id = gen_utils.discord_name_to_id(user2)
        if user1_id and user2_id:
            with MongoClient(config.DB_TOKEN) as db:
                db = db[config.DB_NAME]
                # Change Alias
                query = {"alias": user1_id}
                payload = {"alias": user1_id, "original": user2_id}
                database.set_details(query, payload, "aliases", db)
                # Transfer characters
                database.transfer_characters(server, user1_id, user2, db)
                # Recache the users from the database
                self.bot.user_cache = database.load_all_users(db)
            await context.send(
                ALIAS_CHANGE_SUCCESS.format(user1=user1_id, user2=user2_id)
            )
        else:
            if user1:
                await context.send(USER_NOT_FOUND(user=user2))
            if user2:
                await context.send(USER_NOT_FOUND(user=user1))

    @commands.command(
        name="get_current_gold",
        aliases=["gold"],
        help="Coming soon.",
        brief="How much gold do you have?",
    )
    async def get_current_gold(self, context, user=None):
        server = str(context.guild.id)
        if not user:
            user = str(context.author.id)
        user_id = gen_utils.discord_name_to_id(user)
        if user_id:
            # Get active character
            current = self.bot.get_current_chara(server, user_id)
            if current:
                current_gold = self.bot.character_cache[current].get_gold()
                await context.send(
                    GET_CURRENT_GOLD.format(
                        name=self.bot.character_cache[current].get_name(),
                        user=user_id,
                        gold=current_gold,
                    )
                )
            else:
                await context.send(CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="change_gold",
        aliases=["cg"],
        help="Coming soon.",
        brief="To add or remove gold.",
    )
    @commands.has_permissions(administrator=True)
    async def change_gold(self, context, user, amount):
        server = str(context.guild.id)
        user_id = gen_utils.discord_name_to_id(user)
        amount = int(amount)
        if user_id:
            # Get active character
            current = self.bot.get_current_chara(server, user_id)
            if current:
                current_gold = self.bot.character_cache[current].get_gold()
                new_gold = current_gold + amount
                if new_gold >= 0:
                    # Accepted - write changes to DB
                    self.bot.character_cache[current].set_gold(new_gold)
                    payload = self.bot.character_cache[current].export_stats()
                    query = {"character_id": current}
                    with MongoClient(config.DB_TOKEN) as db:
                        database.set_details(
                            query, payload, "characters", db[config.DB_NAME]
                        )
                    await context.send(
                        CHANGE_GOLD_SUCCESS.format(
                            name=self.bot.character_cache[current].get_name(),
                            user=user_id,
                            amount=amount,
                            new_gold=new_gold,
                        )
                    )
                else:
                    await context.send(
                        NOT_ENOUGH_GOLD.format(
                            name=self.bot.character_cache[current].get_name(),
                            user=user_id,
                            gold=current_gold,
                        )
                    )
            else:
                await context.send(CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="set_gold",
        aliases=["sg"],
        help="Coming soon.",
        brief="To set gold to a particular amount.",
    )
    @commands.has_permissions(administrator=True)
    async def set_gold(self, context, user, amount):
        server = str(context.guild.id)
        user_id = gen_utils.discord_name_to_id(user)
        amount = int(amount)
        if user_id:
            # Get active character
            current = self.bot.get_current_chara(server, user_id)
            if current:
                # Accepted - write changes to DB
                self.bot.character_cache[current].set_gold(amount)
                payload = self.bot.character_cache[current].export_stats()
                query = {"character_id": current}
                with MongoClient(config.DB_TOKEN) as db:
                    database.set_details(
                        query, payload, "characters", db[config.DB_NAME]
                    )
                await context.send(
                    SET_GOLD_SUCCESS.format(
                        name=self.bot.character_cache[current].get_name(),
                        user=user_id,
                        amount=amount,
                    )
                )
            else:
                await context.send(CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="transfer_gold",
        aliases=["transfer"],
        help="Coming soon.",
        brief="To transfer gold between characters.",
    )
    async def transfer_gold(self, context, amount, target):
        server = str(context.guild.id)
        source_user_id = str(context.author.id)
        target_user_id = gen_utils.discord_name_to_id(target)
        amount = int(amount)
        if amount <= 0:
            await context.send(
                GOLD_TRANSFER_AMOUNT_LESS_THAN_ZERO.format(source_user=source_user_id)
            )
        elif source_user_id == target_user_id:
            await context.send(
                GOLD_TRANSFER_SOURCE_AND_TARGET_SAME.format(source_user=source_user_id)
            )
        elif not target_user_id:
            await context.send(USER_NOT_FOUND.format(user=target))
        else:
            # Get active character for source
            source = self.bot.get_current_chara(server, source_user_id)
            # Get active character for target
            source = self.bot.get_current_chara(server, target_user_id)
            if source and target:
                source_gold = self.bot.character_cache[source].get_gold()
                target_gold = self.bot.character_cache[target].get_gold()
                # If a valid transaction
                if source_gold - amount >= 0:
                    # Make changes locally
                    self.bot.character_cache[source].set_gold(source_gold - amount)
                    self.bot.character_cache[target].set_gold(target_gold + amount)
                    # Write changes to DB
                    with MongoClient(config.DB_TOKEN) as db:
                        db = db[config.DB_NAME]
                        payload = self.bot.character_cache[source].export_stats()
                        query = {"character_id": source}
                        database.set_details(query, payload, "characters", db)
                        payload = self.bot.character_cache[target].export_stats()
                        query = {"character_id": target}
                        database.set_details(query, payload, "characters", db)
                    await context.send(
                        GOLD_TRANSFER_SUCCESS.format(
                            source_name=self.bot.character_cache[source].get_name(),
                            target_name=self.bot.character_cache[target].get_name(),
                            source_user=source_user_id,
                            target_user=target_user_id,
                            amount=amount,
                            source_total=source_gold - amount,
                            target_total=target_gold + amount,
                        )
                    )
                else:
                    await context.send(
                        NOT_ENOUGH_GOLD.format(
                            name=self.bot.character_cache[source].get_name(),
                            user=source_user_id,
                            gold=source_gold,
                        )
                    )
            else:
                if not source:
                    await context.send(CHARACTER_NOT_FOUND.format(user=source_user_id))
                if not target:
                    await context.send(CHARACTER_NOT_FOUND.format(user=target_user_id))


async def setup(bot):
    await bot.add_cog(RPGCommands(bot))
