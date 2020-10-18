import sys

sys.path.append("../")
from utils.ability import Ability
from utils.item import Item


class PlayerCharacter:
    def __init__(
        self,
        user,
        name,
        hp,
        attack,
        defense,
        speed,
        dexterity,
        charisma,
        knowledge,
        wisdom,
        strength,
        constitution,
        level,
        gold,
    ):
        self.user = user
        self.name = name
        self.stats = {
            "max_hp": int(hp),
            "current_hp": int(hp),
            "attack": int(attack),
            "defense": int(defense),
            "speed": int(speed),
            "dexterity": int(dexterity),
            "charisma": int(charisma),
            "knowledge": int(knowledge),
            "wisdom": int(wisdom),
            "strength": int(strength),
            "constitution": int(constitution),
        }
        self.stat_lookup = {
            "dex": "dexterity",
            "cha": "charisma",
            "kno": "knowledge",
            "wis": "wisdom",
            "con": "constitution",
            "str": "strength",
        }
        self.level = int(level)
        self.gold = int(gold)
        # self.items = dict()
        # self.abilities = {}  # ability_name:Ability Obj
        # self.weapons = []
        # self.long_rest()

    def info(self):
        return f"""{self.name} ({self.user})
```
+--------------+---------+---+----------------+---------+
| Primary Stat | Value   |   | Secondary Stat | Value   |
+--------------+---------+---+----------------+---------+
| HP           | {self.stats['current_hp']}/{self.stats['max_hp']}{' ' * (7 - len(str(self.stats['current_hp'])) - len(str(self.stats['max_hp'])))}|   | Dexterity      | {self.stats['dexterity']}{' ' * (8 - len(str(self.stats['dexterity'])))}|
| Attack       | {self.stats['attack']}{' ' * (8 - len(str(self.stats['attack'])))}|   | Charisma       | {self.stats['charisma']}{' ' * (8 - len(str(self.stats['charisma'])))}|
| Defense      | {self.stats['defense']}{' ' * (8 - len(str(self.stats['defense'])))}|   | Knowledge      | {self.stats['knowledge']}{' ' * (8 - len(str(self.stats['knowledge'])))}|
| Speed        | {self.stats['speed']}{' ' * (8 - len(str(self.stats['speed'])))}|   | Wisdom         | {self.stats['wisdom']}{' ' * (8 - len(str(self.stats['wisdom'])))}|
| Level        | {self.level}{' ' * (8 - len(str(self.level)))}|   | Strength       | {self.stats['strength']}{' ' * (8 - len(str(self.stats['strength'])))}|
| Gold         | {self.gold}{' ' * (8 - len(str(self.gold)))}|   | Constitution   | {self.stats['constitution']}{' ' * (8 - len(str(self.stats['constitution'])))}|
+--------------+---------+---+----------------+---------+
```"""

    #     def rest_of_the_owl(self):
    #         items_list = "\n".join(
    #             [
    #                 "| "
    #                 + item
    #                 + " " * (32 - len(item))
    #                 + "|"
    #                 + str(amount)
    #                 + " " * (7 - len(str(amount)))
    #                 + "|"
    #                 for item, amount in self.items.items()
    #             ]
    #         )
    #         abilities_list = "\n".join(["* " + ability for ability in self.abilities])
    #         weapons_list = "\n".join(self.weapons)
    #         return f"""
    # ```Items:
    # +--------------------------------+-------+
    # {items_list}
    # +--------------------------------+-------+
    # Abilities:
    # {abilities_list}
    # ------------------------------------------
    # Weapons:
    # {weapons_list}```"""

    # def long_rest(self):
    #     self.current_hp = self.max_hp
    #     for ability in self.abilities:
    #         ability.reset()
    #     return "After taking a long rest you feel completely refreshed. Your stats are back to normal and your powers are at 100%."

    # def short_rest(self):
    #     self.current_hp += 1
    #     # TBF

    # def damage(self, damage):
    #     self.current_hp -= damage
    #     return f"{self.name} took {damage} damage!"

    # def heal(self, heal):
    #     self.current_hp += heal
    #     return f"{self.name} healed {heal} HP!"

    # def add_ability(self, ability_name, ability_object):
    #     # Note keep a dictioanry to look up what the ability is in the main func
    #     if ability_name in self.abilities:
    #         return "You already know this ability."
    #     self.abilities[ability_name] = ability_object
    #     return f"Congratulations, you have learned {ability_name}!"

    # def remove_ability(self, ability):
    #     if ability in self.abilities:
    #         self.abilities.pop(ability)
    #         return f"Well. You forgot {ability}. Why did you do that?"
    #     return "You can't forget an ability if you don't know it."

    # def use_ability(self, ability):
    #     if ability in self.abilities:
    #         use = self.abilities[ability].use()
    #         if use:
    #             return "You successfully used {ability}!"
    #         return "You don't have enough energy to use that ability!"
    #     return "You don't even have that ability m8."

    # def add_item(self, item):
    #     # If item already exists, increment.
    #     pass

    # def remove_item(self, item):
    #     # If item > 1, decrement
    #     # Else delete
    #     pass

    def change_gold(self, amount):
        if self.gold + amount >= 0:
            self.gold += amount
            return True, self.gold
        return False, self.gold

    def get_name(self):
        return self.name

    def get_stat(self, stat):
        return self.stats[self.stat_lookup[stat]]

    def change_user(self, new_user):
        self.user = new_user
