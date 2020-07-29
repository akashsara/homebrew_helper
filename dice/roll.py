import random
import re
import sys

sys.path.append("../")
from utils.logging_util import logger
from utils import gen_utils
from dice import dice

TOO_HIGH = (
    "One or more of your rolls are absurdly high. I'm not rolling that <@{author_id}>."
)
WRONG = "That's not how you do it <@{author_id}>. Your roll should be of the format (roll)(operation)(modifier)(special), where rolls should be of the format XdN (X = Number of Dice; N = Number of Die Faces). Operation is either + or - and modifier is your modifier. Special indicates advantage or disadvantage. Just append your roll with an a or d. Examples: `?r 1d20+2` or `?r 1d20+1d4-2` or `?r 1d20a`."


def normally(roll, author_id):
    roll = dice.roll(roll)
    if roll == "too high":
        return TOO_HIGH.format(author_id=author_id)
    elif roll == "wrong":
        return WRONG.format(author_id=author_id)
    else:
        return f"<@{author_id}>'s Roll:\n```fix\nYou rolled a {roll['user_roll']}.\nYou got: \n{gen_utils.format_rolls(roll['rolls'])}\nYour modifier is: {str(roll['modifier'])}```Your total roll is: **{str(roll['total'])}**"


def with_advantage_or_disadvantage(roll, advantage_or_disadvantage, author_id):
    first_roll = dice.roll(roll)
    # Cover these cases in the 1st roll since we'll get the same for the 2nd
    if first_roll == "too high":
        return TOO_HIGH.format(author_id=author_id)
    elif first_roll == "wrong":
        return WRONG.format(author_id=author_id)
    second_roll = dice.roll(roll)
    base_string = f"<@{author_id}>:\n Attempt 1:\n```fix\nYou rolled a {first_roll['user_roll']}.\nYou got: \n{gen_utils.format_rolls(first_roll['rolls'])}\nYour modifier is: {str(first_roll['modifier'])}\nYour total roll is: {str(first_roll['total'])}```Attempt 2:\n```fix\nYou rolled a {second_roll['user_roll']}.\nYou got: \n{gen_utils.format_rolls(second_roll['rolls'])}\nYour modifier is: {str(second_roll['modifier'])}\nYour total roll is: {str(second_roll['total'])}```"
    if advantage_or_disadvantage == "a":
        return (
            base_string
            + f"Your final roll is: **{max(first_roll['total'], second_roll['total'])}**."
        )
    else:
        return (
            base_string
            + f"Your final roll is: **{min(first_roll['total'], second_roll['total'])}**."
        )


def and_repeat(roll, num_repeats, author_id):
    first_roll = dice.roll(roll)
    # Cover these cases in the 1st roll since we'll get the same for the 2nd
    if first_roll == "too high":
        return TOO_HIGH.format(author_id=author_id)
    elif first_roll == "wrong":
        return WRONG.format(author_id=author_id)
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
