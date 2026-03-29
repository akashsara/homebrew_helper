import os
import sys

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("HOMEBREW_HELPER_TOKEN")
DB_TOKEN = os.environ.get("DATABASE_TOKEN")
DB_NAME = "homebrew_helper"


def require_config() -> None:
    """Exit the process if required secrets are not set."""
    missing = []
    if not TOKEN:
        missing.append("HOMEBREW_HELPER_TOKEN")
    if not DB_TOKEN:
        missing.append("DATABASE_TOKEN")
    if missing:
        print(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Set them in your environment or a .env file.",
            file=sys.stderr,
        )
        raise SystemExit(1)
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
