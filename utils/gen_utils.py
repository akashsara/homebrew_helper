import os
import sys
import joblib
import uuid
from functools import partial
from collections import defaultdict
sys.path.append("../")
from utils.logging_util import logger

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


def load_files(file_root_dir, file_dict):
    dicts = {
        "users": defaultdict(partial(defaultdict, get_default_user)),
        "characters": dict(),
        "abilities": defaultdict(partial(defaultdict, dict)),
        "items": defaultdict(partial(defaultdict, dict)),
        "aliases": defaultdict(list),
    }
    for key, value in file_dict.items():
        file_path = os.path.join(f"{file_root_dir}/{value}")
        if os.path.exists(file_path):
            logger.info(f"Loading from {file_path}")
            dicts[key] = joblib.load(file_path)
    return (
        dicts["users"],
        dicts["characters"],
        dicts["abilities"],
        dicts["items"],
        dicts["aliases"],
    )


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
    full_text = []
    ending = []
    for item in rolls:
        roll = item["user_roll"]
        all_in_one = []
        for _, y in item["rolls"]:
            all_in_one.extend(y)
        modifier = pad(str(item["modifier"]), 2, "left")
        total = pad(str(item["total"]), 5, "left")
        ending.append(item["total"])
        full_text.append(f"{roll} : {total} :: {modifier} + {all_in_one}")
    ending = f"Final Rolls: **{ending}**"
    return full_text, ending
