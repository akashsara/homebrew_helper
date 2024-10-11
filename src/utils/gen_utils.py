import re
import uuid
from typing import Dict, List
import logging


# Create logger
def create_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    )
    logger.addHandler(handler)
    return logger


def generate_id() -> str:
    return str(uuid.uuid4())


def generate_unique_id(generated: set, max_retries=100) -> str:
    id_ = generate_id()
    for _ in range(max_retries):
        if id_ not in generated:
            return id_
        id_ = generate_id()
    return RuntimeError("Unable to generate unique ID")


def get_default_user() -> Dict:
    return {"active": None, "characters": []}


def discord_name_to_id(name: str) -> str:
    search = re.findall(r"\d+", name)
    if search:
        return str(search[0])


def format_stat(name):
    return name.replace("_", " ").title()


def pad(text_to_pad: str, length_to_pad_to: int, direction: str) -> str:
    if direction == "left":
        return (" " * (length_to_pad_to - len(text_to_pad))) + text_to_pad
    return text_to_pad + (" " * (length_to_pad_to - len(text_to_pad)))


def format_rolls(rolls: List[str]) -> str:
    new_roll = []
    for item in rolls:
        key, value = item
        num_dice, die_size = key.split("d")
        num_dice = pad(num_dice, 2, "left")
        die_size = pad(die_size, 3, "right")
        total = pad(str(sum(value)), 5, "left")
        new_roll.append(f"{num_dice}d{die_size}: {total} :: {value}")
    return "\n".join(new_roll)


def format_repeated_rolls(rolls: List[Dict]) -> str:
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
