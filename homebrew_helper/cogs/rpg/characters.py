import asyncio
import json
import logging
from typing import List

from discord.ext import commands
import homebrew_helper.templates as templates
from homebrew_helper.utils import database, gen_utils, player_character


def _get_owned_characters(user_info, character_cache) -> List[player_character.PlayerCharacter]:
    characters = []
    for character_id in user_info.get("characters", []):
        character = character_cache.get(character_id)
        if character:
            characters.append(character)
    return characters


def _find_owned_character_matches(user_info, character_cache, query: str):
    query = query.strip().lower()
    matches = []
    for character_id in user_info.get("characters", []):
        character = character_cache.get(character_id)
        if not character:
            continue
        name = character.get_name()
        lowered_name = name.lower()
        if query == character_id.lower() or query == lowered_name:
            return [character]
        if query in lowered_name or character_id.lower().startswith(query):
            matches.append(character)
    return matches


def _format_character_matches(characters) -> str:
    return ", ".join(f"{character.get_name()} (`{character.character_id}`)" for character in characters)


def _format_owned_character_list(characters, active_character_id: str, user_id: str) -> str:
    lines = [templates.CHARACTER_LIST_HEADER.format(count=len(characters), user=user_id)]
    for character in characters:
        marker = " [active]" if character.character_id == active_character_id else ""
        lines.append(f"- {character.get_name()} (`{character.character_id}`){marker}")
    return "\n".join(lines)


def _split_rename_payload(payload: str):
    if "|" not in payload:
        return None, None
    query, new_name = payload.split("|", 1)
    return query.strip(), new_name.strip()


def _is_yes_response(content: str) -> bool:
    return content.lower().strip().startswith("y")


def _resolve_target_user_id(context, raw_text: str):
    raw_text = raw_text.strip()
    if not raw_text:
        return str(context.author.id), raw_text
    first_token, separator, remainder = raw_text.partition(" ")
    target_user_id = gen_utils.discord_name_to_id(first_token)
    is_admin = getattr(context.author.guild_permissions, "administrator", False)
    if separator and target_user_id and is_admin:
        return target_user_id, remainder.strip()
    return str(context.author.id), raw_text


# Ref: https://stackoverflow.com/questions/65595213/how-to-add-shared-cooldown-to-multiple-discord-py-commands
class RPGCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("bot.rpg_commands")

    @commands.command(
        name="create",
        aliases=["create_character", "create_char", "cc"],
        help="Admin only. Create a character for a user with `!create @user <json>`.",
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
                        await context.send(templates.CREATE_CHARACTER_CONFIRM_PROMPT)
                        await context.send(character.info())
                        def confirm_check(m):
                            return (
                                m.author == context.author
                                and m.channel == context.channel
                            )

                        try:
                            message = await self.bot.wait_for(
                                "message", timeout=60, check=confirm_check
                            )
                            if message and message.content.lower().strip().startswith(
                                "y"
                            ):
                                # Write character to DB
                                repo = self.bot.repo
                                payload = character.export_stats()
                                repo.save_character(uuid, payload)
                                user_info = repo.get_user(server, user_id)
                                if user_info:
                                    user_info["characters"].append(uuid)
                                else:
                                    user_info = {
                                        "server": server,
                                        "user": user_id,
                                        "characters": [uuid],
                                    }
                                user_info["active"] = uuid
                                repo.save_user(server, user_id, user_info)
                                # Update local caches
                                self.bot.character_cache[uuid] = character
                                if server not in self.bot.user_cache:
                                    self.bot.user_cache[server] = {}
                                self.bot.user_cache[server][user_id] = user_info
                                await context.send(templates.CREATE_CHARACTER_SUCCESS)
                            else:
                                await context.send(templates.CREATE_CHARACTER_CANCEL)
                        except asyncio.TimeoutError:
                            await context.send(templates.CREATE_CHARACTER_CANCEL)
                        except Exception as e:
                            self.logger.warning(
                                "Failed to create character: %s", e, exc_info=True
                            )
                            await context.send("UNKNOWN ERROR! Report & Contact Lan!!")
                    else:
                        await context.send(
                            templates.CREATE_CHARACTER_INVALID_STATS.format(
                                user=context.author.id, error=result["error"]
                            )
                        )
                except json.decoder.JSONDecodeError:
                    await context.send(templates.CREATE_CHARACTER_JSON_ERROR)
            else:
                await context.send(templates.CREATE_CHARACTER_NO_INFO.format(user=user_id))
        else:
            await context.send(templates.USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="info",
        help="Show the active character for you or another user.",
        brief="To get character info.",
    )
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
                await context.send(templates.CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(templates.USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="chars",
        aliases=["list_characters", "characters"],
        help="List the characters owned by you or another user.",
        brief="List a user's characters.",
    )
    async def list_characters(self, context, user=None):
        if user:
            user_id = gen_utils.discord_name_to_id(user)
        else:
            user_id = str(context.author.id)
        if not user_id:
            await context.send(templates.USER_NOT_FOUND.format(user=user))
            return

        server = str(context.guild.id)
        user_info = self.bot.user_cache.get(server, {}).get(user_id, {})
        owned_characters = _get_owned_characters(user_info, self.bot.character_cache)
        if not owned_characters:
            await context.send(templates.CHARACTER_NOT_FOUND.format(user=user_id))
            return

        await context.send(
            _format_owned_character_list(
                owned_characters,
                user_info.get("active"),
                user_id,
            )
        )

    @commands.command(
        name="rename",
        aliases=["rename_character", "rename_char", "rc"],
        help="Rename one of your characters with `<current name or id> | <new name>`.",
        brief="Rename one of your characters.",
    )
    async def rename_character(self, context, *, payload):
        server = str(context.guild.id)
        acting_user_id = str(context.author.id)
        target_user_id, payload = _resolve_target_user_id(context, payload)
        user_info = self.bot.user_cache.get(server, {}).get(target_user_id, {})
        owned_characters = _get_owned_characters(user_info, self.bot.character_cache)
        if not owned_characters:
            await context.send(
                templates.CHARACTER_SWITCH_NO_OWNED_CHARACTERS.format(user=target_user_id)
            )
            return

        query, new_name = _split_rename_payload(payload)
        if not query or new_name is None:
            await context.send(templates.CHARACTER_RENAME_USAGE.format(user=acting_user_id))
            return
        if not new_name:
            await context.send(templates.CHARACTER_RENAME_EMPTY.format(user=acting_user_id))
            return

        matches = _find_owned_character_matches(
            user_info, self.bot.character_cache, query
        )
        if not matches:
            await context.send(
                templates.CHARACTER_RENAME_NOT_FOUND.format(
                    user=target_user_id, query=query
                )
            )
            return
        if len(matches) > 1:
            await context.send(
                templates.CHARACTER_RENAME_AMBIGUOUS.format(
                    user=target_user_id,
                    query=query,
                    matches=_format_character_matches(matches),
                )
            )
            return

        selected = matches[0]
        old_name = selected.get_name()
        selected.character_info["name"] = new_name
        self.bot.repo.save_character(selected.character_id, selected.export_stats())
        await context.send(
            templates.CHARACTER_RENAME_SUCCESS.format(
                user=acting_user_id,
                target_user=target_user_id,
                old_name=old_name,
                new_name=new_name,
                character_id=selected.character_id,
            )
        )

    @commands.command(
        name="switch",
        aliases=["switch_character", "switch_char", "sc"],
        help="Set your active character by name or character ID.",
        brief="Switch your active character.",
    )
    async def switch_character(self, context, *, query):
        server = str(context.guild.id)
        acting_user_id = str(context.author.id)
        target_user_id, query = _resolve_target_user_id(context, query)
        user_info = self.bot.user_cache.get(server, {}).get(target_user_id, {})
        owned_characters = _get_owned_characters(user_info, self.bot.character_cache)
        if not owned_characters:
            await context.send(
                templates.CHARACTER_SWITCH_NO_OWNED_CHARACTERS.format(user=target_user_id)
            )
            return

        matches = _find_owned_character_matches(
            user_info, self.bot.character_cache, query
        )
        if not matches:
            await context.send(
                templates.CHARACTER_SWITCH_NOT_FOUND.format(
                    user=target_user_id, query=query
                )
            )
            return
        if len(matches) > 1:
            await context.send(
                templates.CHARACTER_SWITCH_AMBIGUOUS.format(
                    user=target_user_id,
                    query=query,
                    matches=_format_character_matches(matches),
                )
            )
            return

        selected = matches[0]
        user_info["active"] = selected.character_id
        self.bot.repo.save_user(server, target_user_id, user_info)
        self.bot.user_cache.setdefault(server, {})[target_user_id] = user_info
        await context.send(
            templates.CHARACTER_SWITCH_SUCCESS.format(
                user=acting_user_id,
                target_user=target_user_id,
                name=selected.get_name(),
                character_id=selected.character_id,
            )
        )

    @commands.command(
        name="delete",
        aliases=["delete_character", "delete_char", "dc"],
        help="Delete one of your characters by name or character ID.",
        brief="Delete one of your characters.",
    )
    async def delete_character(self, context, *, query):
        server = str(context.guild.id)
        acting_user_id = str(context.author.id)
        target_user_id, query = _resolve_target_user_id(context, query)
        user_info = self.bot.user_cache.get(server, {}).get(target_user_id, {})
        owned_characters = _get_owned_characters(user_info, self.bot.character_cache)
        if not owned_characters:
            await context.send(
                templates.CHARACTER_SWITCH_NO_OWNED_CHARACTERS.format(user=target_user_id)
            )
            return

        matches = _find_owned_character_matches(
            user_info, self.bot.character_cache, query
        )
        if not matches:
            await context.send(
                templates.CHARACTER_DELETE_NOT_FOUND.format(
                    user=target_user_id, query=query
                )
            )
            return
        if len(matches) > 1:
            await context.send(
                templates.CHARACTER_DELETE_AMBIGUOUS.format(
                    user=target_user_id,
                    query=query,
                    matches=_format_character_matches(matches),
                )
            )
            return

        selected = matches[0]
        selected_name = selected.get_name()
        await context.send(
            templates.CHARACTER_DELETE_CONFIRM_PROMPT.format(
                user=acting_user_id,
                name=selected_name,
                character_id=selected.character_id,
            )
        )
        def confirm_check(m):
            return m.author == context.author and m.channel == context.channel

        try:
            message = await self.bot.wait_for(
                "message", timeout=60, check=confirm_check
            )
            if not message or not _is_yes_response(message.content):
                await context.send(
                    templates.CHARACTER_DELETE_CANCEL.format(user=acting_user_id)
                )
                return
        except asyncio.TimeoutError:
            await context.send(
                templates.CHARACTER_DELETE_CANCEL.format(user=acting_user_id)
            )
            return

        user_info["characters"] = [
            character_id
            for character_id in user_info.get("characters", [])
            if character_id != selected.character_id
        ]
        if user_info.get("active") == selected.character_id:
            user_info["active"] = (
                user_info["characters"][0] if user_info["characters"] else None
            )
        self.bot.repo.delete_character(selected.character_id)
        self.bot.repo.save_user(server, target_user_id, user_info)
        self.bot.character_cache.pop(selected.character_id, None)
        self.bot.user_cache.setdefault(server, {})[target_user_id] = user_info
        await context.send(
            templates.CHARACTER_DELETE_SUCCESS.format(
                user=acting_user_id,
                target_user=target_user_id,
                name=selected_name,
                character_id=selected.character_id,
            )
        )

    @commands.command(
        name="saving_throw",
        aliases=["st", "stat_roll"],
        help="Roll a saving throw or ability check with `!st <stat> [modifiers]`, including `a` or `d` for advantage or disadvantage.",
        brief="To roll a saving throw for your character.",
    )
    async def saving_throw(self, context, stat=None, modifiers=""):
        server = str(context.guild.id)
        user_id = gen_utils.discord_name_to_id(str(context.author.id))
        if not stat:
            await context.send(
                f"Hey <@{context.author.id}>, to do a saving throw or ability check do `!st <stat> (a|d)`. You can also add an a or d to signify advantage or disadvantage."
            )
            return
        # Parse out modifiers and advantage/disadvantage
        modifiers, advantage_or_disadvantage = gen_utils.parse_modifiers(modifiers)
        # Get active character
        current = self.bot.get_current_chara(server, user_id)
        if current:
            stat_name, stat_path = self.bot.character_cache[current].resolve_stat_name(
                stat
            )
            if stat_name:
                stat_bonus = self.bot.character_cache[current].get_stat(stat_path)
                sign = "+" if stat_bonus >= 0 else ""
                query = f"1d20{sign}{stat_bonus}{modifiers}{advantage_or_disadvantage}"
                await context.send(f"Rolling for {gen_utils.format_stat(stat_name)}.")
                await context.invoke(self.bot.get_command("roll"), query)
            else:
                await context.send(templates.INVALID_STAT.format(user=user_id))
        else:
            await context.send(templates.CHARACTER_NOT_FOUND.format(user=user_id))

    @commands.command(
        name="attack",
        help="Roll an attack for your active character, with optional modifiers and advantage or disadvantage.",
        brief="To make an attack roll.",
    )
    async def attack(self, context, modifiers=""):
        server = str(context.guild.id)
        user_id = gen_utils.discord_name_to_id(str(context.author.id))
        # Parse out modifiers and advantage/disadvantage
        modifiers, advantage_or_disadvantage = gen_utils.parse_modifiers(modifiers)
        # Get active character
        current = self.bot.get_current_chara(server, user_id)
        if current:
            stat_bonus = self.bot.character_cache[current].get_attack()
            sign = "+" if stat_bonus >= 0 else ""
            query = f"1d20{sign}{stat_bonus}{modifiers}{advantage_or_disadvantage}"
            await context.invoke(self.bot.get_command("roll"), query)
        else:
            await context.send(templates.CHARACTER_NOT_FOUND.format(user=user_id))

    @commands.command(
        name="setstat",
        aliases=["change_stat", "stat_change"],
        help="Admin only. Set a stat on a user's active character with `!setstat @user <stat> <value>`.",
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
                stat_name, stat_path = self.bot.character_cache[
                    current
                ].resolve_stat_name(stat)
                if stat_name:
                    self.bot.character_cache[current].set_stat(stat_path, value)
                    character_name = self.bot.character_cache[current].get_name()
                    payload = self.bot.character_cache[current].export_stats()
                    self.bot.repo.save_character(current, payload)
                    await context.send(
                        templates.STAT_CHANGE_SUCCESSFUL.format(
                            character_name=character_name,
                            stat_name=gen_utils.format_stat(stat_name),
                            user=user_id,
                            value=value,
                        )
                    )
                else:
                    await context.send(templates.INVALID_STAT.format(user=user_id))
            else:
                await context.send(templates.CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(templates.USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="alias",
        aliases=["add_alias", "add_alt", "aa"],
        help="Admin only. Link two users so the first user's characters are transferred to the second user.",
        brief="To add nickname.",
    )
    @commands.has_permissions(administrator=True)
    async def add_alias(self, context, user1, user2):
        server = str(context.guild.id)
        user1_id = gen_utils.discord_name_to_id(user1)
        user2_id = gen_utils.discord_name_to_id(user2)
        if user1_id and user2_id:
            repo = self.bot.repo
            repo.set_alias(user1_id, user2_id)
            repo.transfer_user_characters(server, user1_id, user2_id)
            self.bot.user_cache = database.load_all_users(repo.raw_db)
            self.bot.character_cache = database.hydrate_character_models(repo.raw_db)
            await context.send(
                templates.ALIAS_CHANGE_SUCCESS.format(user1=user1_id, user2=user2_id)
            )
        else:
            if not user1_id:
                await context.send(templates.USER_NOT_FOUND.format(user=user1))
            if not user2_id:
                await context.send(templates.USER_NOT_FOUND.format(user=user2))

    @commands.command(
        name="gold",
        aliases=["get_current_gold"],
        help="Show how much gold the active character has for you or another user.",
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
                    templates.GET_CURRENT_GOLD.format(
                        name=self.bot.character_cache[current].get_name(),
                        user=user_id,
                        gold=current_gold,
                    )
                )
            else:
                await context.send(templates.CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(templates.USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="goldadd",
        aliases=["change_gold", "cg"],
        help="Admin only. Add or remove gold from a user's active character with `!goldadd @user <amount>`.",
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
                    self.bot.repo.save_character(current, payload)
                    await context.send(
                        templates.CHANGE_GOLD_SUCCESS.format(
                            name=self.bot.character_cache[current].get_name(),
                            user=user_id,
                            amount=amount,
                            new_gold=new_gold,
                        )
                    )
                else:
                    await context.send(
                        templates.NOT_ENOUGH_GOLD.format(
                            name=self.bot.character_cache[current].get_name(),
                            user=user_id,
                            gold=current_gold,
                        )
                    )
            else:
                await context.send(templates.CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(templates.USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="goldset",
        aliases=["set_gold", "sg"],
        help="Admin only. Set the gold total for a user's active character with `!goldset @user <amount>`.",
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
                self.bot.repo.save_character(current, payload)
                await context.send(
                    templates.SET_GOLD_SUCCESS.format(
                        name=self.bot.character_cache[current].get_name(),
                        user=user_id,
                        amount=amount,
                    )
                )
            else:
                await context.send(templates.CHARACTER_NOT_FOUND.format(user=user_id))
        else:
            await context.send(templates.USER_NOT_FOUND.format(user=user))

    @commands.command(
        name="pay",
        aliases=["transfer_gold", "transfer"],
        help="Transfer gold from your active character to another user's active character with `!pay <amount> @user`.",
        brief="To transfer gold between characters.",
    )
    async def transfer_gold(self, context, amount, target):
        server = str(context.guild.id)
        source_user_id = str(context.author.id)
        target_user_id = gen_utils.discord_name_to_id(target)
        amount = int(amount)
        if amount <= 0:
            await context.send(
                templates.GOLD_TRANSFER_AMOUNT_LESS_THAN_ZERO.format(source_user=source_user_id)
            )
        elif source_user_id == target_user_id:
            await context.send(
                templates.GOLD_TRANSFER_SOURCE_AND_TARGET_SAME.format(source_user=source_user_id)
            )
        elif not target_user_id:
            await context.send(templates.USER_NOT_FOUND.format(user=target))
        else:
            source = self.bot.get_current_chara(server, source_user_id)
            target = self.bot.get_current_chara(server, target_user_id)
            if source and target:
                source_gold = self.bot.character_cache[source].get_gold()
                target_gold = self.bot.character_cache[target].get_gold()
                if source_gold - amount < 0:
                    await context.send(
                        templates.NOT_ENOUGH_GOLD.format(
                            name=self.bot.character_cache[source].get_name(),
                            user=source_user_id,
                            gold=source_gold,
                        )
                    )
                elif self.bot.repo.transfer_gold_between_characters(
                    source, target, amount
                ):
                    self.bot.character_cache[source].set_gold(source_gold - amount)
                    self.bot.character_cache[target].set_gold(target_gold + amount)
                    await context.send(
                        templates.GOLD_TRANSFER_SUCCESS.format(
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
                        "Gold transfer failed (database rejected the update). "
                        "Try again or contact an admin."
                    )
            else:
                if not source:
                    await context.send(templates.CHARACTER_NOT_FOUND.format(user=source_user_id))
                if not target:
                    await context.send(templates.CHARACTER_NOT_FOUND.format(user=target_user_id))


async def setup(bot):
    await bot.add_cog(RPGCommands(bot))
