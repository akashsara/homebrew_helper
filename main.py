import os
import re
import discord
import random
from discord.ext.commands import Bot
from player_character import PlayerCharacter
from ability import Ability
from item import Item

TOKEN = os.environ.get("HOMEBREW_HELPER_TOKEN")
BOT_PREFIX = ("?",)
roll_format = r"(\d+)d(\d+)([+-])?(\d+)?"
client = Bot(command_prefix=BOT_PREFIX)


@client.command(name="roll", aliases=["r"])
async def roll(context, roll):
    match = re.match(roll_format, roll)
    author = context.author
    if match:
        rolls = []
        match = [x for x in match.groups() if x]
        num_dice = int(match[0])
        die_type = int(match[1])
        if len(match) > 2:
            modifier_type = (
                lambda x, y: x + y if match[2] == "+" else lambda x, y: x - y
            )
            modifier_amount = int(match[3])
        else:
            modifier_type = lambda x, y: x + y
            modifier_amount = 0
        # Roll Dice N times
        rolls = [random.randint(1, die_type) for i in range(num_dice)]
        final_value = modifier_type(sum(rolls), modifier_amount)
        print(rolls, sum(rolls))
        await context.send(f"@{author}, your final roll is a {final_value}. You rolled: {rolls}")
    else:
        await context.send(
            f"That's not how you do it @{author}. Your roll should be of the format XDN or XDN+Y. X = Number of dice, N = Size of die, Y = Modifier."
        )

if __name__ == "__main__":
    print("Booting up client..")
    client.run(TOKEN)
