import random
import re
import sys
from typing import Dict, Tuple, List

import config
import error_messages
import templates
from utils import gen_utils

sys.path.append("../")

import logging

logger = logging.getLogger(__name__)


def roll_dice(num_dice: int, die_type: int) -> List[int]:
    return [random.randint(1, die_type) for _ in range(num_dice)]


def resolve_operation(accumulator: int, operation: str, value: int) -> int:
    if operation == "+":
        return accumulator + value
    return accumulator - value


def parse_roll(roll_string: str, operation: str) -> Tuple[List[int], int, int, str]:
    dice_value = 0
    modifier = 0
    status = "OK"
    # if this is a dice roll operation
    if "d" in roll_string:
        num_dice, die_type = [int(x) for x in roll_string.split("d")]
        # check if valid roll
        if (
            num_dice > config.DICE_ROLL_MAX_DICE
            or die_type > config.DICE_ROLL_LARGEST_DIE
        ):
            status = "too high"
        else:
            all_rolls = roll_dice(num_dice, die_type)
            dice_value = resolve_operation(0, operation, sum(all_rolls))
        result = [(roll_string, all_rolls)]
    # if this is a modifier update operation
    else:
        modifier = resolve_operation(0, operation, int(roll_string))
        result = []
    # Save roll and result in a variable
    return result, dice_value, modifier, status


def roll_handler(input_roll: str) -> Dict:
    """
    Iterates through the given string sequentially.
    The only allowed characters here are numbers, d, +, and -.
    If we encounter a number or "d", we just append it to the current string.
    Else, we resolve the roll.
    """
    # Validate if this is even a roll
    if not config.VALID_ROLL_CHARACTERS.issuperset(set(input_roll)):
        return {"status": "wrong"}
    try:
        completed_rolls = []
        total_dice_value = 0
        total_modifier = 0
        operation = "+"
        current_roll = ""
        for char in input_roll:
            if char not in ["+", "-"]:
                current_roll += char
            else:
                result, dice_value, modifier, status = parse_roll(
                    current_roll, operation
                )
                total_dice_value += dice_value
                total_modifier += modifier
                completed_rolls.extend(result)
                # if any of the rolls are invalid, raise an error immediately
                if status != "OK":
                    return {"status": status}
                # (Re)set variables for next iteration
                operation = char
                current_roll = ""
        if current_roll:
            result, dice_value, modifier, status = parse_roll(current_roll, operation)
            total_dice_value += dice_value
            total_modifier += modifier
            completed_rolls.extend(result)
            # if any of the rolls are invalid, raise an error immediately
            if status != "OK":
                return {"status": status}
        return {
            "user_roll": input_roll,
            "rolls": completed_rolls,
            "modifier": total_modifier,
            "total": total_dice_value + total_modifier,
            "status": "OK",
        }
    except Exception as e:
        logger.debug(e)
        return {"status": "wrong"}


def roll_and_repeat(roll: str, n_repeats: int) -> List[Dict]:
    first_result = roll_handler(roll)
    if first_result.get("status") != "OK":
        return first_result
    # Repeat the roll n_repeats - 1 times.
    # We don't check roll status again since we validated it already
    list_of_rolls = [first_result] + [roll_handler(roll) for _ in range(n_repeats - 1)]
    return list_of_rolls


def dice_roll_formatter(
    roll: str,
    author_id: str,
    roll_type: str,
    results: List[Dict],
    final_result: List[int],
) -> str:
    if roll_type == "normal":
        return templates.NORMAL_ROLL.format(
            author_id=author_id,
            user_roll=roll,
            result=gen_utils.format_rolls(results[0]["rolls"]),
            modifier=results[0]["modifier"],
            total=final_result[0],
        )
    elif roll_type == "adv_disadv":
        return templates.ROLL_WITH_ADV_DISADV.format(
            author_id=author_id,
            user_first_roll=roll,
            first_result=gen_utils.format_rolls(results[0]["rolls"]),
            first_modifier=results[0]["modifier"],
            first_total=results[0]["total"],
            user_second_roll=roll,
            second_result=gen_utils.format_rolls(results[1]["rolls"]),
            second_modifier=results[1]["modifier"],
            second_total=results[1]["total"],
            final_result=final_result[0],
        )
    elif roll_type == "repeat":
        # Only partial templates here since we're building this programatically
        all_rolls = gen_utils.format_repeated_rolls(results)
        outputs = [
            templates.ROLL_WITH_REPEATS_STARTING_STRING.format(
                author_id=author_id, roll=roll
            ),
            all_rolls,
            templates.ROLL_WITH_REPEATS_ENDING_STRING.format(final_rolls=final_result),
        ]
        return "\n".join(outputs)


def roll_wrapper(
    roll: str,
    author_id: str,
    roll_type: str,
    n_repeats: str = "1",
    is_advantage: bool = False,
) -> str:
    # First pass of error checks - pre-roll
    n_dice = sum(int(x) for x in re.findall(r"(\d+)d", roll))
    n_repeats = int(n_repeats) if n_repeats.isdigit() else n_repeats

    # If the number of repeats is invalid
    if not isinstance(n_repeats, int) or n_repeats < 1:
        return {
            "error": True,
            "message": error_messages.ROLL_WITH_REPEAT_INVALID_DIGIT.format(
                author_id=author_id
            ),
        }
    # If there are too many repetitions
    elif (n_dice * n_repeats) > config.DICE_ROLL_MAX_DICE:
        return {
            "error": True,
            "message": error_messages.TOO_MANY_DICE.format(
                author_id=author_id, max_dice=config.DICE_ROLL_MAX_DICE
            ),
        }
    # Invalid roll type
    elif roll_type not in ["normal", "adv_disadv", "repeat"]:
        return {
            "error": True,
            "message": error_messages.INVALID_ROLL_TYPE.format(author_id=author_id),
        }

    # Roll dice
    # N repeats of a dice roll is the generalized function here
    if roll_type == "normal":
        results = roll_and_repeat(roll, n_repeats=1)
        # Final result is just the total of the roll
        final_result = [results[0]["total"]]
    elif roll_type == "adv_disadv":
        results = roll_and_repeat(roll, n_repeats=2)
        # Final result is the max/min of the two rolls
        final_result = [
            (
                max(results[0]["total"], results[1]["total"])
                if is_advantage
                else min(results[0]["total"], results[1]["total"])
            )
        ]
    elif roll_type == "repeat":
        results = roll_and_repeat(roll, n_repeats=n_repeats)
        # Final result is a list of all rolls
        final_result = [result["total"] for result in results]

    # Ensure all rolls were successful
    status = "OK"
    for result in results:
        if result["status"] != "OK":
            status = result["status"]
            break

    # Validate status and handle post-roll error cases
    # Too high of a dice value
    if status == "too high":
        return {
            "error": True,
            "message": error_messages.DICE_TOO_HIGH.format(
                author_id=author_id,
                largest_die=config.DICE_ROLL_LARGEST_DIE,
                max_dice=config.DICE_ROLL_MAX_DICE,
            ),
        }
    # Error in dice command
    elif status == "wrong":
        return {
            "error": True,
            "message": error_messages.WRONG_DICE_COMMAND.format(author_id=author_id),
        }
    # All other errors
    elif status != "OK":
        return {"error": True, "message": error_messages.UNKNOWN_ERROR}

    # Format output and return
    output_string = dice_roll_formatter(
        roll, author_id, roll_type, results, final_result
    )
    output_dict = {
        "error": False,
        "message": output_string,
        "raw": results,
        "final_result": final_result,
    }
    return output_dict
