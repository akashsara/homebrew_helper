from typing import Union, Dict, Any
from src.utils import gen_utils

def validate_character(chara) -> Dict[str, str]:
    required = ["name", "attack", "armor_class", "speed", "level", "gold"]
    for req in required:
        if req not in chara.keys():
            return {"status": False, "error": f"{req} is missing from character."}
        else:
            if req == "name":
                if not isinstance(chara["name"], str):
                    return {"status": False, "error": "name is not a string."}
            else:
                if not isinstance(chara[req], int):
                    return {"status": False, "error": f"{req} is not an integer."}
    if not isinstance(chara["stats"], dict):
        return {"status": False, "error": f"Stats is not a dictionary."}
    for stat in chara["stats"]:
        if isinstance(chara["stats"][stat], dict):
            for key in chara["stats"][stat].keys():
                if not isinstance(chara["stats"][stat][key], int):
                    return {"status": False, "error": f"{stat} is not an integer."}
        elif not isinstance(chara["stats"][stat], int):
            return {"status": False, "error": f"{stat} is not an integer."}
    return {"status": True, "error": "None"}


def create_spaced_line(stat, value, value_at=25, level=0):
    n_tabs = "\t" * level
    return f"{n_tabs}{stat}:{' ' * (value_at - len(stat) - len(str(value)) - 1 - (len(n_tabs) * 4))}{value}"


class PlayerCharacter:
    def __init__(
        self,
        user: str = "",
        character_id: str = "",
        character_info: dict = {
            "name": "",
            "hp": 0,
            "attack": 0,
            "armor_class": 0,
            "speed": 0,
            "level": 0,
            "gold": 0,
            "stats": {},
        },
    ):
        """
        character_info must be a dict with the keys specified by the default.
        Stats are up to the creator to set.
        You can use a dictionary for a stat like so:
        "charisma": {
            "base": 2,
            "deception": 4,
            "intimidation": 4,
            "performance": 2,
            "persuasion": 2,
        }
        Base refers to the actual modifier for Charisma above.
        """
        # Everything below this is stored in a DB
        if "name" not in character_info:
            return ValueError("No name found in character information.")
        elif "stats" not in character_info:
            return ValueError("No stats found in character information.")
        elif "gold" not in character_info:
            return ValueError("No gold found in character information.")
        self.user = user
        self.character_id = character_id
        self.character_info = character_info

    def export_stats(self) -> dict:
        return {
            "user": self.user,
            "character_id": self.character_id,
            "character_info": self.character_info,
        }

    def import_stats(self, character: dict):
        self.user = character["user"]
        self.character_id = character["character_id"]
        self.character_info = character["character_info"]

    def info(self) -> str:
        output = [
            f"{self.character_info.get('name')} (<@!{self.user}>)",
            "```",
            create_spaced_line("Level", self.character_info["level"]),
            create_spaced_line("Gold", self.character_info["gold"]),
            "---" * 10,
            create_spaced_line("Health", self.character_info["hp"]),
            create_spaced_line("Armor Class", self.character_info["armor_class"]),
            create_spaced_line("Attack", self.character_info["attack"]),
            create_spaced_line("Speed", self.character_info["speed"]),
            "---" * 10,
        ]
        for stat, value in self.character_info["stats"].items():
            if isinstance(value, dict):
                output.append(create_spaced_line(gen_utils.format_stat(stat), value["base"]))
                for substat, subvalue in value.items():
                    if substat != "base":
                        output.append(
                            create_spaced_line(gen_utils.format_stat(substat), subvalue, level=1)
                        )
                output.append("---" * 10)
            else:
                output.append(create_spaced_line(gen_utils.format_stat(stat), value))
        output.append("```")
        return "\n".join(output)

    def change_user(self, new_user: str):
        self.user = new_user

    def resolve_stat_name(self, candidate: str) -> Union[str, bool]:
        """
        Checks if user input exact matches the stat.
        If not then it checks for a partial match.
        If there is exactly one partial match, it works with that.
        If there are none or more than one matches, return False.
        """
        partial_matches = []
        for stat_name, value in self.character_info["stats"].items():
            # Go through subkeys if dict
            if isinstance(value, dict):
                if candidate == stat_name:
                    # Exact match
                    return f"{stat_name}__base"
                elif stat_name.startswith(candidate):
                    # Partial match
                    partial_matches.append(f"{stat_name}__base")
                for substat_name in value.keys():
                    # Exact match
                    if candidate == substat_name:
                        return f"{stat_name}__{substat_name}"
                    # Partial match
                    elif substat_name.startswith(candidate):
                        partial_matches.append(f"{stat_name}__{substat_name}")
            # Exact match
            elif candidate == stat_name:
                return candidate
            # Partial match
            elif stat_name.startswith(candidate):
                partial_matches.append(stat_name)
        if len(partial_matches) == 1:
            return partial_matches[0]
        return False

    def get_stat(self, stat: str) -> Union[str, bool]:
        if "__" in stat:
            key, subkey = stat.split("__")
            return self.character_info["stats"][key][subkey]
        return self.character_info["stats"][stat]

    def set_stat(self, stat: str, value: int) -> bool:
        if "__" in stat:
            key, subkey = stat.split("__")
            self.character_info["stats"][key][subkey] = value
        self.character_info["stats"][stat] = value

    def get_gold(self) -> int:
        return self.character_info["gold"]

    def set_gold(self, amount: int):
        self.character_info["gold"] = amount

    def get_name(self) -> str:
        return self.character_info["name"]
