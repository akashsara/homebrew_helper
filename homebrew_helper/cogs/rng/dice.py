import asyncio
import logging
import random
from collections import Counter
from typing import Dict, List

import homebrew_helper.config as config
import homebrew_helper.templates as templates
from discord.ext import commands
from homebrew_helper.utils import dice, gen_utils

# Initiative dict keys: Discord user snowflake, or "npc:{name} {n}" for NPC slots.
NPC_PREFIX = "npc:"

_INIT_ROLL_STATE = {
    config.INITIATIVE_REACTIONS["normal_roll"]: (False, False),
    config.INITIATIVE_REACTIONS["advantage_roll"]: (True, True),
    config.INITIATIVE_REACTIONS["disadvantage_roll"]: (True, False),
}


def _normalize_roll_text(roll_parts) -> str:
    return "".join(roll_parts).lower().replace(" ", "")


def _looks_like_dice_roll(roll: str) -> bool:
    if roll[-1:] in ["a", "d"]:
        roll = roll[:-1]
    return bool(roll) and config.VALID_ROLL_CHARACTERS.issuperset(set(roll))


def _npc_key(npc_name: str, index: int) -> str:
    return f"{NPC_PREFIX}{npc_name} {index + 1}"


def _initiative_player_label(bot, server: str, reaction_user) -> str:
    user_id = str(reaction_user.id)
    current = bot.get_current_chara(server, user_id)
    if current:
        return bot.character_cache[current].get_name()
    return str(reaction_user.display_name)


def _format_initiative_table_row(
    result: int, all_rolls: List[str], player_name: str
) -> str:
    result = str(result).rjust(2)
    if len(all_rolls) == 2:
        r0 = all_rolls[0].rjust(2)
        r1 = all_rolls[1].rjust(2)
        rolls_fmt = f"({r0},{r1})"
    else:
        rolls_fmt = " " * 7
    if len(player_name) < 36:
        player_name = player_name.ljust(36)
    elif len(player_name) > 36:
        player_name = player_name[:36]
    return f"\n| {result} {rolls_fmt}   | {player_name} |"


def _build_initiative_table(roll_list: List[dict]) -> str:
    lines = []
    for player_roll in sorted(roll_list, key=lambda x: x["result"], reverse=True):
        lines.append(
            _format_initiative_table_row(
                player_roll["result"],
                player_roll["all_rolls"],
                player_roll["player"],
            )
        )
    return "".join(lines)


def _collect_initiative_rolls(
    players_to_roll_for: Dict[str, List[bool]],
    player_labels: Dict[str, str],
) -> List[dict]:
    roll_list = []
    for player_key, (use_advantage, is_advantage) in players_to_roll_for.items():
        display_name = player_labels.get(player_key, player_key)
        author_for_roll = (
            player_key[len(NPC_PREFIX) :]
            if player_key.startswith(NPC_PREFIX)
            else player_key
        )
        if use_advantage:
            outcome = dice.roll_wrapper(
                "1d20", author_for_roll, "adv_disadv", is_advantage=is_advantage
            )
            player_name = f"{display_name} ({'A' if is_advantage else 'D'})"
        else:
            outcome = dice.roll_wrapper("1d20", author_for_roll, "normal")
            player_name = display_name
        roll_list.append(
            {
                "player": player_name,
                "result": outcome["final_result"][0],
                "all_rolls": [str(x["total"]) for x in outcome["raw"]],
            }
        )
    return roll_list


# Ref: https://stackoverflow.com/questions/65595213/how-to-add-shared-cooldown-to-multiple-discord-py-commands
class RNGCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("bot.rng_commands")

    @commands.command(
        name="coin_toss",
        aliases=["cointoss", "toss", "flip", "cointoin", "toincoss", "toss_coin"],
        help="Tosses a coin and returns the outcome heards or tails.",
        brief="To toss one or many coin(s).",
    )
    async def coin_toss(self, context, *num_tosses):
        num_tosses = "".join(num_tosses)
        num_tosses = 1 if not num_tosses.isdigit() else int(num_tosses)
        if num_tosses > config.COIN_TOSS_MAX_TOSSES:
            result = templates.COIN_TOSS_TOO_MANY_TOSSES.format(
                author_id=context.author.id, max_tosses=config.COIN_TOSS_MAX_TOSSES
            )
        else:
            tosses = random.choices(population=[True, False], k=num_tosses)
            counts = Counter(tosses)
            raw_output = "\n".join(
                ["+ Heads" if toss else "- Tails" for toss in tosses]
            )
            result = templates.COIN_TOSS_RESULT.format(
                author_id=context.author.id,
                num_tosses=num_tosses,
                raw_output=raw_output,
                num_heads=counts[True],
                num_tails=counts[False],
            )
        await context.send(result)

    @commands.command(
        name="roll_dice",
        aliases=["roll", "r", "R", "ROLL", "Roll"],
        help="Rolls the dice and returns the outcome.",
        brief="To roll one or many dice(s).",
    )
    async def roll(self, context, *roll):
        roll_parts = [part.lower().replace(" ", "") for part in roll]
        if await self._try_character_roll(context, roll_parts):
            return

        roll = _normalize_roll_text(roll_parts)
        author = context.author
        self.logger.info("Roll: %s (%s) :: %s", author, author.id, roll)
        if not roll:
            err = dice.roll_wrapper("?", author.id, "normal")
            await context.send(err["message"])
            return
        if roll[-1] in ["a", "d"]:
            result = dice.roll_wrapper(
                roll[:-1], author.id, "adv_disadv", is_advantage=roll[-1] == "a"
            )
        elif "r" in roll:
            roll, n_repeats = roll.split("r")
            result = dice.roll_wrapper(roll, author.id, "repeat", n_repeats=n_repeats)
        else:
            result = dice.roll_wrapper(roll, author.id, "normal")
        await context.send(result["message"])

    async def _try_character_roll(self, context, roll_parts) -> bool:
        if not roll_parts:
            return False

        command_name = roll_parts[0]
        modifiers = _normalize_roll_text(roll_parts[1:])

        if command_name == "attack":
            attack_command = self.bot.get_command("attack")
            if attack_command:
                await context.invoke(attack_command, modifiers)
                return True

        roll = _normalize_roll_text(roll_parts)
        if _looks_like_dice_roll(roll):
            return False

        saving_throw_command = self.bot.get_command("saving_throw")
        if saving_throw_command:
            await context.invoke(saving_throw_command, command_name, modifiers)
            return True

        return False

    @commands.command(
        name="roll_initiative",
        aliases=["initiative", "ri", "RI", "rolli"],
        help="Gets the order in which the players will make their move in battle.",
        brief="To get the roll initiative.",
    )
    async def roll_initiative(self, context, npc_count=0, npc_name_template="NPC"):
        try:
            npc_count = int(npc_count)
        except ValueError:
            await context.send(templates.ROLL_INITIATIVE_INVALID_NPCS)
            return
        npc_name = npc_name_template[:30]
        if npc_count > config.INITIATIVE_MAX_NPCS:
            npc_count = config.INITIATIVE_MAX_NPCS
            await context.send(
                templates.ROLL_INITIATIVE_TOO_MANY_NPCS.format(
                    max_npcs=config.INITIATIVE_MAX_NPCS
                )
            )
        players_to_roll_for: Dict[str, List[bool]] = {}
        player_labels: Dict[str, str] = {}
        for i in range(npc_count):
            key = _npc_key(npc_name, i)
            players_to_roll_for[key] = [False, False]
            player_labels[key] = f"{npc_name} {i + 1}"
        player_reactions = {
            key: config.INITIATIVE_REACTIONS["normal_roll"]
            for key in players_to_roll_for
        }

        roll_initiative_message = await context.send(
            templates.ROLL_INITIATIVE_INSTRUCTIONS
        )

        for reaction in config.INITIATIVE_REACTIONS.values():
            await roll_initiative_message.add_reaction(reaction)

        def check(reaction, user):
            return user != self.bot.user

        server = str(context.guild.id)

        try:
            while True:
                reaction, reaction_user = await self.bot.wait_for(
                    "reaction_add", timeout=60, check=check
                )
                emoji = str(reaction.emoji)
                player_key = str(reaction_user.id)
                stop = config.INITIATIVE_REACTIONS["stop_roll"]
                if player_key in players_to_roll_for and emoji != stop:
                    current_reaction = player_reactions[player_key]
                    await roll_initiative_message.remove_reaction(
                        current_reaction, reaction_user
                    )
                    del players_to_roll_for[player_key]
                    del player_reactions[player_key]
                    del player_labels[player_key]

                roll_state = _INIT_ROLL_STATE.get(emoji)
                if roll_state is not None:
                    use_adv, is_adv = roll_state
                    players_to_roll_for[player_key] = [use_adv, is_adv]
                    player_reactions[player_key] = emoji
                    player_labels[player_key] = _initiative_player_label(
                        self.bot, server, reaction_user
                    )
                elif emoji == stop and reaction_user == context.author:
                    break
        except asyncio.TimeoutError:
            await context.send(templates.ROLL_INITIATIVE_TIMEOUT)

        if len(players_to_roll_for) != 0:
            roll_list = _collect_initiative_rolls(players_to_roll_for, player_labels)
            output_string = _build_initiative_table(roll_list)
            await context.send(
                templates.ROLL_INITIATIVE_START_STRING
                + output_string
                + templates.ROLL_INITIATIVE_END_STRING
            )
        else:
            await context.send(templates.ROLL_INITIATIVE_NOT_ENOUGH_PLAYERS)


async def setup(bot):
    await bot.add_cog(RNGCommands(bot))
