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

TOO_HIGH = (
    "One or more of your rolls are absurdly high. I'm not rolling that <@{author_id}>."
)

WRONG = "That's not how you do it <@{author_id}>. Your roll should be of the format (roll)(operation)(modifier)(special), where rolls should be of the format XdN (X = Number of Dice; N = Number of Die Faces). Operation is either + or - and modifier is your modifier. Special indicates advantage or disadvantage. Just append your roll with an a or d. Examples: `?r 1d20+2` or `?r 1d20+1d4-2` or `?r 1d20a`."

######################################################################
############# Used Specifically For Certain Bot Commands #############
######################################################################
RICK_ROLL_LYRICS = [
    [
        "♫♫♫ We're no strangers to love ♫♫♫",
        "♫♫♫ You know the rules and so do I ♫♫♫",
    ],
    [
        "♫♫♫ A full commitment's what I'm thinking of ♫♫♫",
        "♫♫♫ You wouldn't get this from any other guy ♫♫♫",
    ],
    [
        "♫♫♫ I just wanna tell you how I'm feeling ♫♫♫",
        "♫♫♫ Gotta make you understand ♫♫♫",
    ],
    [
        "♫♫♫ Never gonna give you up ♫♫♫",
        "♫♫♫ Never gonna let you down ♫♫♫",
        "♫♫♫ Never gonna run around and desert you ♫♫♫",
        "♫♫♫ Never gonna make you cry ♫♫♫",
        "♫♫♫ Never gonna say goodbye ♫♫♫",
        "♫♫♫ Never gonna tell a lie and hurt you ♫♫♫",
    ],
]

ORACLE_ANSWERS = [
    "HELL YEAH",
    "Yes.",
    "That is an excellent question.",
    "Wouldn't you like to know, weather boy?",
    "No.",
    "Nope.",
    "Nah man.",
    "Yup yup!",
    "Maybe",
    "idk lol",
    "Things will make sense when they make sense.",
    "It's all part of the plan",
    "It is known.",
    "No chance.",
    "Yes, 100%.",
    "Ask again later.",
    "The Oracle you're trying to reach is currently unavailable. Please hold the line or try again later.",
    "Don't count on it.",
    "My sources say no.",
    "Don't try to play the fool with me Nikesh.",
]
