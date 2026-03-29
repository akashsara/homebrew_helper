"""Shared helpers. Logging: call ``configure_logging`` once at process entry (e.g. ``run_bot``);
elsewhere use ``get_logger(__name__)`` and never attach handlers to library loggers."""

import logging
import re
import uuid
from typing import Dict, List, Optional, Tuple

_LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s: %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    """
    Initialize root logging once. Idempotent: if handlers already exist (e.g. tests), only
    updates the root level so re-imports do not stack duplicate handlers.
    """
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return
    logging.basicConfig(level=level, format=_LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger; do not add handlers here (root owns output)."""
    return logging.getLogger(name)


def generate_id() -> str:
    return str(uuid.uuid4())


def generate_unique_id(generated: set, max_retries=100) -> str:
    id_ = generate_id()
    for _ in range(max_retries):
        if id_ not in generated:
            return id_
        id_ = generate_id()
    raise RuntimeError("Unable to generate unique ID")


def get_default_user() -> Dict:
    return {"active": None, "characters": []}


def discord_name_to_id(name: str) -> Optional[str]:
    search = re.findall(r"\d+", name)
    if search:
        return str(search[0])
    return None


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


def parse_modifiers(modifiers: str) -> Tuple[str, str]:
    advantage_or_disadvantage = ""
    if len(modifiers) > 0:
        if modifiers[0] not in ["+", "-"]:
            modifiers = "+" + modifiers
        if modifiers[-1] in ["a", "d"]:
            advantage_or_disadvantage = modifiers[-1]
            modifiers = modifiers[:-1]
    return modifiers, advantage_or_disadvantage
