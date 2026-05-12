from homebrew_helper.cogs.rng import dice as rng_dice
import asyncio
from types import SimpleNamespace


def test_npc_key_format():
    assert rng_dice._npc_key("Goblin", 0) == "npc:Goblin 1"
    assert rng_dice._npc_key("Goblin", 2) == "npc:Goblin 3"


def test_format_initiative_table_row_normal_roll():
    row = rng_dice._format_initiative_table_row(14, ["12"], "Alice")
    assert "14" in row
    assert "Alice" in row


def test_format_initiative_table_row_advantage_two_rolls():
    row = rng_dice._format_initiative_table_row(18, ["17", "18"], "Bob")
    assert "(17,18)" in row.replace(" ", "")


def test_format_initiative_table_row_truncates_long_name():
    long_name = "x" * 50
    row = rng_dice._format_initiative_table_row(10, ["5"], long_name)
    assert len([c for c in row if c == "x"]) <= 36


def test_build_initiative_table_sorted_by_result():
    rolls = [
        {"result": 5, "all_rolls": ["5"], "player": "Low"},
        {"result": 20, "all_rolls": ["20"], "player": "High"},
    ]
    table = rng_dice._build_initiative_table(rolls)
    assert table.index("High") < table.index("Low")


class _FakeContext:
    def __init__(self):
        self.invocations = []

    async def invoke(self, command, *args):
        self.invocations.append((command, args))


class _FakeBot:
    def __init__(self):
        self.commands = {
            "attack": SimpleNamespace(name="attack"),
            "saving_throw": SimpleNamespace(name="saving_throw"),
        }

    def get_command(self, name):
        return self.commands.get(name)


def test_roll_dispatches_attack_keyword_to_attack_command():
    cog = rng_dice.RNGCommands(_FakeBot())
    context = _FakeContext()

    handled = asyncio.run(cog._try_character_roll(context, ["attack", "a"]))

    assert handled is True
    assert context.invocations == [(cog.bot.commands["attack"], ("a",))]


def test_roll_dispatches_stat_keyword_to_saving_throw_command():
    cog = rng_dice.RNGCommands(_FakeBot())
    context = _FakeContext()

    handled = asyncio.run(cog._try_character_roll(context, ["strength", "a"]))

    assert handled is True
    assert context.invocations == [
        (cog.bot.commands["saving_throw"], ("strength", "a"))
    ]


def test_roll_dispatches_stat_with_bonus_and_advantage_to_saving_throw_command():
    cog = rng_dice.RNGCommands(_FakeBot())
    context = _FakeContext()

    handled = asyncio.run(cog._try_character_roll(context, ["strength", "+3", "a"]))

    assert handled is True
    assert context.invocations == [
        (cog.bot.commands["saving_throw"], ("strength", "+3a"))
    ]


def test_roll_does_not_dispatch_dice_rolls_to_character_commands():
    cog = rng_dice.RNGCommands(_FakeBot())
    context = _FakeContext()

    handled = asyncio.run(cog._try_character_roll(context, ["2d6+3"]))

    assert handled is False
    assert context.invocations == []


def test_roll_does_not_dispatch_advantage_dice_rolls_to_character_commands():
    cog = rng_dice.RNGCommands(_FakeBot())
    context = _FakeContext()

    handled = asyncio.run(cog._try_character_roll(context, ["1d20+2a"]))

    assert handled is False
    assert context.invocations == []
