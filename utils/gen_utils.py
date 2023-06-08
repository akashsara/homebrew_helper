import os
import re
import sys
import uuid
from collections import defaultdict
from functools import partial

import joblib

sys.path.append("../")
import logging

logger = logging.getLogger(__name__)


def generate_id():
    return str(uuid.uuid4())


def generate_unique_id(generated):
    id_ = generate_id()
    while id_ in generated:
        id_ = generate_id()
    return id_


def save_file(data, file_path):
    logger.info(f"Saving to {file_path}")
    joblib.dump(data, file_path)


def get_default_user():
    return {"active": None, "characters": []}


def discord_name_to_id(name):
    search = re.findall("\d+", name)
    logger.info(f"Found {search} from {name}.")
    if search:
        return str(search[0])
    return None


def pad(text_to_pad, length_to_pad_to, direction):
    if direction == "left":
        return (" " * (length_to_pad_to - len(text_to_pad))) + text_to_pad
    return text_to_pad + (" " * (length_to_pad_to - len(text_to_pad)))


def format_rolls(rolls):
    new_roll = []
    for item in rolls:
        key, value = item
        num_dice, die_size = key.split("d")
        num_dice = pad(num_dice, 2, "left")
        die_size = pad(die_size, 3, "right")
        total = pad(str(sum(value)), 5, "left")
        new_roll.append(f"{num_dice}d{die_size}: {total} :: {value}")
    return "\n".join(new_roll)


def format_repeated_rolls(rolls):
    all_text = []
    for item in rolls:
        roll = item["user_roll"]
        all_in_one = []
        for _, y in item["rolls"]:
            all_in_one.extend(y)
        modifier = pad(str(item["modifier"]), 2, "left")
        total = pad(str(item["total"]), 5, "left")
        all_text.append(f"{roll} : {total} :: {modifier} + {all_in_one}")
    return "\n".join(all_text)
