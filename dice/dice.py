import random
import re
import sys

sys.path.append("../")
from utils.logging_util import logger
from config import *

roll_format = r"\d+d\d+"
valid_characters = set(str(x) for x in range(0, 10)).union(
    {"+", "-", "d", " ", "(", ")"}
)
def split_the_roll(roll):
    num_dice, die_type = roll.split("d")
    return int(num_dice), int(die_type)


def make_the_roll(num_dice, die_type):
    return [random.randint(1, die_type) for i in range(num_dice)]


def resolve_operation(accumulator, operation, value):
    if operation == "+":
        return accumulator + value
    return accumulator - value


def parse_roll(roll, final_value, total_modifier, operation, all_rolls):
    if "d" in roll:
        logger.debug("Dice roll detected.")
        num_dice, die_type = split_the_roll(roll)
        if num_dice > DICE_ROLL_MAX_DICE or die_type > DICE_ROLL_LARGEST_DIE:
            return "too high", 0, 0
        roll_results = make_the_roll(num_dice, die_type)
        all_rolls.append((roll, roll_results))
        final_value = resolve_operation(final_value, operation, sum(roll_results))
        logger.debug(f"Rolled: {roll_results}")
    else:
        logger.debug("Modifier update.")
        total_modifier = resolve_operation(total_modifier, operation, int(roll))
        logger.debug(f"New Modifier: {total_modifier}")
    return all_rolls, final_value, total_modifier


def roll(user_rolled_a):
    # Validate if this is even a roll
    if not valid_characters.issuperset(set(user_rolled_a)):
        return "wrong"
    try:
        all_rolls = []
        final_value = 0
        total_modifier = 0
        operation = "+"
        current_roll = ""
        for char in user_rolled_a:
            logger.debug(f"Current Character: {char}. Current window: {current_roll}")
            if char not in ["+", "-"]:
                current_roll += char
            else:
                all_rolls, final_value, total_modifier = parse_roll(
                    current_roll, final_value, total_modifier, operation, all_rolls
                )
                if all_rolls == "too high":
                    return "too high"
                operation = char
                current_roll = ""
        if current_roll:
            all_rolls, final_value, total_modifier = parse_roll(
                current_roll, final_value, total_modifier, operation, all_rolls
            )
            if all_rolls == "too high":
                return "too high"
        return {
            "user_roll": user_rolled_a,
            "rolls": all_rolls,
            "modifier": total_modifier,
            "total": final_value + total_modifier,
        }
    except Exception as e:
        logger.debug(e)
        return "wrong"
