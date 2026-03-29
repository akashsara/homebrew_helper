from homebrew_helper.cogs.rng import dice as rng_dice


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
