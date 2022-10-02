import os

TOKEN = os.environ.get("HOMEBREW_HELPER_TOKEN")
DB_TOKEN = os.environ.get("DATABASE_TOKEN")
BOT_PREFIX = ("?", "!")
ALLOWED_STATS = [
    "dex",
    "con",
    "cha",
    "kno",
    "wis",
    "str",
    "atk",
    "def",
    "speed",
    "max_hp",
    "current_hp",
]

VALID_ROLL_CHARACTERS = set(str(x) for x in range(0, 10)).union(
    {"+", "-", "d", " ", "(", ")"}
)

COIN_TOSS_MAX_TOSSES = 20
INITIATIVE_MAX_NPCS = 20
DICE_ROLL_MAX_DICE = 50
DICE_ROLL_LARGEST_DIE = 100
DISCORD_ID_REGEX = "(<@!\d+>)"

TOO_HIGH = (
    "One or more of your rolls are absurdly high. I'm not rolling that <@{author_id}>."
)

WRONG = "That's not how you do it <@{author_id}>. Your roll should be of the format (roll)(operation)(modifier)(special), where rolls should be of the format XdN (X = Number of Dice; N = Number of Die Faces). Operation is either + or - and modifier is your modifier. Special indicates advantage or disadvantage. Just append your roll with an a or d. Examples: `?r 1d20+2` or `?r 1d20+1d4-2` or `?r 1d20a`."