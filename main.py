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


@client.command(name="roll", aliases=["r", "R", "ROLL", "Roll"])
async def roll(context, *roll):
    roll = "".join(roll)
    roll = roll.replace(" ", "")
    match = re.match(roll_format, roll)
    author = context.author
    print(author, roll)
    if match:
        rolls = []
        match = [x for x in match.groups() if x]
        num_dice = int(match[0])
        die_type = int(match[1])
        if num_dice > 50 or die_type > 1000:
            await context.send(f"I'm not rolling that absurd number <@{author.id}>.")
        if len(match) > 2:
            if match[2] == "+":
                modifier_amount = int(match[3])
            else:
                modifier_amount = int("-" + match[3])
        else:
            modifier_amount = 0
        # Roll Dice N times
        rolls = [random.randint(1, die_type) for i in range(num_dice)]
        final_value = sum(rolls) + modifier_amount
        await context.send(
            f"<@{author.id}>'s Roll:\n```fix\nYou rolled a {roll}.\nYou got: {', '.join(str(x) for x in rolls)}\nYour modifier is: {str(modifier_amount)}```Your total roll is: **{final_value}**"
        )
    else:
        await context.send(
            f"That's not how you do it <@{author.id}>. Your roll should be of the format XDN or XDN+-Y. X = Number of dice, N = Size of die, Y = Modifier."
        )

if __name__ == "__main__":
    print("Booting up client..")
    client.run(TOKEN)
