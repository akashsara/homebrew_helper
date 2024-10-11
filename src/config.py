import os

TOKEN = os.environ.get("HOMEBREW_HELPER_TOKEN")
DB_TOKEN = os.environ.get("DATABASE_TOKEN")
BOT_PREFIX = ("?", "!")

VALID_ROLL_CHARACTERS = set(str(x) for x in range(0, 10)).union(
    {"+", "-", "d", " ", "(", ")"}
)

COIN_TOSS_MAX_TOSSES = 20
INITIATIVE_MAX_NPCS = 20
DICE_ROLL_MAX_DICE = 50
DICE_ROLL_LARGEST_DIE = 100
DISCORD_ID_REGEX = r"(<@!\d+>)"

INITIATIVE_REACTIONS = {
    "normal_roll": "⚔️",
    "advantage_roll": "👍",
    "disadvantage_roll": "👎",
    "stop_roll": "🛑",
}
