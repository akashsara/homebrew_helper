import random
import re
import sys

sys.path.append("../")
from utils.logging_util import logger
from utils import gen_utils
from dice import dice
from config import *

def validate_and_roll(roll, author_id):
    roll = dice.roll(roll)
    if roll == "too high":
        return False, TOO_HIGH.format(author_id=author_id, largest_die=DICE_ROLL_LARGEST_DIE, max_dice=DICE_ROLL_MAX_DICE)
    elif roll == "wrong":
        return False, WRONG.format(author_id=author_id)
    else:
        return True, roll

def normally(roll, author_id):
    valid, outcome = validate_and_roll(roll, author_id)
    if valid:
        return f"<@{author_id}>'s Roll:\n```fix\nYou rolled a {outcome['user_roll']}.\nYou got: \n{gen_utils.format_rolls(outcome['rolls'])}\nYour modifier is: {str(outcome['modifier'])}```Your total roll is: **{str(outcome['total'])}**"
    else:
        return outcome


def with_advantage_or_disadvantage(roll, use_advantage, author_id, return_rolls_as_list=False):
    # Validate only once because the 2nd roll is the same
    valid, outcome = validate_and_roll(roll, author_id)
    if not valid:
        return outcome
    else:
        first_roll = outcome
    second_roll = dice.roll(roll)
    base_string = f"<@{author_id}>:\n Attempt 1:\n```fix\nYou rolled a {first_roll['user_roll']}.\nYou got: \n{gen_utils.format_rolls(first_roll['rolls'])}\nYour modifier is: {str(first_roll['modifier'])}\nYour total roll is: {str(first_roll['total'])}```Attempt 2:\n```fix\nYou rolled a {second_roll['user_roll']}.\nYou got: \n{gen_utils.format_rolls(second_roll['rolls'])}\nYour modifier is: {str(second_roll['modifier'])}\nYour total roll is: {str(second_roll['total'])}```"
    # Calculate final number
    result = max(first_roll['total'], second_roll['total']) if use_advantage else min(first_roll['total'], second_roll['total'])
    # Certain functions require a list of rolls instead of a return string.
    if return_rolls_as_list:
        return [result, [first_roll['total'], second_roll['total']]]
    else:
        return base_string + f"Your final roll is: **{result}**."


def and_repeat(roll, num_repeats, author_id):
    # Validate only once because the other rolls are the same
    valid, outcome = validate_and_roll(roll, author_id)
    if not valid:
        return outcome
    else:
        first_roll = outcome
    # Repeat the roll n_repeats - 1 times.
    list_of_rolls = [first_roll]
    for _ in range(num_repeats - 1):
        list_of_rolls.append(dice.roll(roll))
    main_rolls, ending = gen_utils.format_repeated_rolls(list_of_rolls)
    outputs = (
        [f"<@{author_id}>'s Roll:", "```fix", f"You rolled {roll}."]
        + main_rolls
        + ["```" + ending]
    )
    return "\n".join(outputs)
