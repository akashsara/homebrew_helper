import asyncio
import logging
import random
from collections import Counter

import src.config as config
import src.templates as templates
from discord.ext import commands
from src.utils import database, dice, gen_utils
import pymongo


# Ref: https://stackoverflow.com/questions/65595213/how-to-add-shared-cooldown-to-multiple-discord-py-commands
class RNGCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("bot.rng_commands")

    @commands.command(
        name="coin_toss",
        aliases=["cointoss", "toss", "flip", "cointoin"],
        help="Tosses a coin and returns the outcome heards or tails.",
        brief="To toss one or many coin(s).",
    )
    async def coin_toss(self, context, *num_tosses):
        num_tosses = "".join(num_tosses)
        num_tosses = 1 if not num_tosses.isdigit() else int(num_tosses)
        if num_tosses > config.COIN_TOSS_MAX_TOSSES:
            result = templates.COIN_TOSS_TOO_MANY_TOSSES.format(
                author_id=context.author_id, max_tosses=config.COIN_TOSS_MAX_TOSSES
            )
        else:
            tosses = random.choices(population=[True, False], k=num_tosses)
            counts = Counter(tosses)
            raw_output = "\n".join(
                ["+ Heads" if toss else "- Tails" for toss in tosses]
            )
            result = templates.COIN_TOSS_RESULT.format(
                author_id=context.author_id,
                num_tosses=num_tosses,
                raw_output=raw_output,
                num_heads=counts[True],
                num_tails=counts[False],
            )
        await context.send("\n".join(result))

    @commands.command(
        name="roll_dice",
        aliases=["roll", "r", "R", "ROLL", "Roll"],
        help="Rolls the dice and returns the outcome.",
        brief="To roll one or many dice(s).",
    )
    async def roll(self, context, *roll):
        roll = "".join(roll).lower().replace(" ", "")
        author = context.author
        self.logger.info(f"Roll: {author.name + '#' + author.discriminator} :: {roll}")
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

    @commands.command(
        name="roll_initiative",
        aliases=["initiative", "ri", "RI", "rolli"],
        help="Gets the order in which the players will make their move in battle.",
        brief="To get the roll initiative.",
    )
    async def roll_initiative(self, context, npc_count=0, npc_name_template="NPC"):
        # We first ensure that there's no errors with the number/names of NPCs
        try:
            npc_count = int(npc_count)
        except ValueError:
            await context.send(templates.ROLL_INITIATIVE_INVALID_NPCS)
            return
        # We take only up to 30 characters to preserve table formatting.
        npc_name = npc_name_template[:30]
        # We have a hard limit on the number of NPCs we roll for.
        if npc_count > config.INITIATIVE_MAX_NPCS:
            npc_count = config.INITIATIVE_MAX_NPCS
            await context.send(
                templates.ROLL_INITIATIVE_TOO_MANY_NPCS.format(
                    max_npcs=config.INITIATIVE_MAX_NPCS
                )
            )
        # Include the NPCs in the list of players we roll for.
        players_to_roll_for = {
            f"{npc_name} {i+1}": [False, False] for i in range(npc_count)
        }
        # Store the actual reactions separately for easier management
        player_reactions = {
            f"{npc_name} {i+1}": config.INITIATIVE_REACTIONS["normal_roll"]
            for i in range(npc_count)
        }

        # Send instruction messages to the channel
        roll_initiative_message = await context.send(
            templates.ROLL_INITIATIVE_INSTRUCTIONS
        )

        # Add emoji to the message for people to click on
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
                user = gen_utils.discord_name_to_id(str(reaction_user.id))
                # Get active character if it exists
                current = (
                    self.bot.user_cache.get(server, {}).get(user, {}).get("active")
                )
                author_id = (
                    self.bot.character_cache[current].get_name()
                    if current
                    else str(reaction_user.name)
                )
                # Test if user input has already happened
                # if it has, erase the previous input
                # Only if this isn't a stop_roll reaction though
                if (
                    author_id in players_to_roll_for
                    and emoji != config.INITIATIVE_REACTIONS["stop_roll"]
                ):
                    current_reaction = player_reactions[author_id]
                    await roll_initiative_message.remove_reaction(
                        current_reaction, reaction_user
                    )
                    del players_to_roll_for[author_id]
                    del player_reactions[author_id]

                # Identify reaction and track it
                if emoji == config.INITIATIVE_REACTIONS["normal_roll"]:
                    players_to_roll_for[author_id] = [False, False]
                    player_reactions[author_id] = config.INITIATIVE_REACTIONS[
                        "normal_roll"
                    ]
                elif emoji == config.INITIATIVE_REACTIONS["advantage_roll"]:
                    players_to_roll_for[author_id] = [True, True]
                    player_reactions[author_id] = config.INITIATIVE_REACTIONS[
                        "advantage_roll"
                    ]
                elif emoji == config.INITIATIVE_REACTIONS["disadvantage_roll"]:
                    players_to_roll_for[author_id] = [True, False]
                    player_reactions[author_id] = config.INITIATIVE_REACTIONS[
                        "disadvantage_roll"
                    ]
                # Stop if the creator used the stop_roll emoji
                elif (
                    emoji == config.INITIATIVE_REACTIONS["stop_roll"]
                    and reaction_user == context.author
                ):
                    break
        except asyncio.TimeoutError:
            await context.send(templates.ROLL_INITIATIVE_TIMEOUT)

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
            for player_roll in sorted(
                roll_list, key=lambda x: x["result"], reverse=True
            ):
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
            await context.send(templates.ROLL_INITIATIVE_NOT_ENOUGH_PLAYERS)


async def setup(bot):
    await bot.add_cog(RNGCommands(bot))
