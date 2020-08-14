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
        self.max_hp = int(hp)
        self.current_hp = self.max_hp
        self.attack = int(attack)
        self.defense = int(defense)
        self.speed = int(speed)
        self.dexterity = int(dexterity)
        self.charisma = int(charisma)
        self.knowledge = int(knowledge)
        self.wisdom = int(wisdom)
        self.strength = int(strength)
        self.constitution = int(constitution)
        self.level = int(level)
        self.gold = int(gold)
        # self.items = dict()
        # self.abilities = {}  # ability_name:Ability Obj
        # self.weapons = []
        # self.long_rest()

    def info(self):
        return f"""{self.name} (<@{self.user}>)
```
+--------------+---------+---+----------------+---------+
| Primary Stat | Value   |   | Secondary Stat | Value   |
+--------------+---------+---+----------------+---------+
| HP           | {self.current_hp}/{self.max_hp}{' ' * (7 - len(str(self.current_hp)) - len(str(self.max_hp)))}|   | Dexterity      | {self.dexterity}{' ' * (8 - len(str(self.dexterity)))}|
| Attack       | {self.attack}{' ' * (8 - len(str(self.attack)))}|   | Charisma       | {self.charisma}{' ' * (8 - len(str(self.charisma)))}|
| Defense      | {self.defense}{' ' * (8 - len(str(self.defense)))}|   | Knowledge      | {self.knowledge}{' ' * (8 - len(str(self.knowledge)))}|
| Speed        | {self.speed}{' ' * (8 - len(str(self.speed)))}|   | Wisdom         | {self.wisdom}{' ' * (8 - len(str(self.wisdom)))}|
| Level        | {self.level}{' ' * (8 - len(str(self.level)))}|   | Strength       | {self.strength}{' ' * (8 - len(str(self.strength)))}|
| Gold         | {self.gold}{' ' * (8 - len(str(self.gold)))}|   | Constitution   | {self.constitution}{' ' * (8 - len(str(self.constitution)))}|
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

    def change_gold(self, amount, operator):
        if operator == "-" and self.gold >= amount:
            self.gold -= amount
            return True
        elif operator == "+":
            self.gold += amount
            return True
        return False
