import random
import re

roll_format = r"(\d+)d(\d+)([+-])?(\d+)?"


def roll(roll):
    match = re.match(roll_format, roll)
    if match:
        rolls = []
        match = [x for x in match.groups() if x]
        num_dice = int(match[0])
        die_type = int(match[1])
        if num_dice > 50 or die_type > 1000:
            return "too high"
        if len(match) > 2:
            if match[2] == "+":
                modifier_amount = int(match[3])
            else:
                modifier_amount = int("-" + match[3])
        else:
            modifier_amount = 0
        rolls = [random.randint(1, die_type) for i in range(num_dice)]
        final_value = sum(rolls) + modifier_amount
        return roll, rolls, modifier_amount, final_value

    else:
        return "wrong"

