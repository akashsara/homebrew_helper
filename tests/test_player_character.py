import pytest

from homebrew_helper.utils.player_character import (
    PlayerCharacter,
    create_spaced_line,
    validate_character,
)


def _minimal_info(name="Test", **kwargs):
    base = {
        "name": name,
        "hp": 10,
        "attack": 2,
        "armor_class": 14,
        "speed": 30,
        "level": 2,
        "gold": 50,
        "stats": {"strength": 2},
    }
    base.update(kwargs)
    return base


def test_create_spaced_line_contains_label_and_value():
    line = create_spaced_line("Level", 5)
    assert "Level" in line
    assert "5" in line


def test_player_character_init_requires_name():
    with pytest.raises(ValueError, match="No name"):
        PlayerCharacter(character_info={"gold": 0, "stats": {}})


def test_player_character_init_requires_stats():
    with pytest.raises(ValueError, match="No stats"):
        PlayerCharacter(character_info={"name": "x", "gold": 0})


def test_player_character_init_requires_gold():
    with pytest.raises(ValueError, match="No gold"):
        PlayerCharacter(
            character_info={"name": "x", "stats": {}},
        )


def test_player_character_export_import_roundtrip():
    info = _minimal_info()
    pc = PlayerCharacter(user="111", character_id="cid-1", character_info=info)
    exported = pc.export_stats()
    other = PlayerCharacter()
    other.import_stats(exported)
    assert other.user == "111"
    assert other.character_id == "cid-1"
    assert other.character_info["name"] == "Test"


def test_player_character_info_includes_key_sections():
    info = _minimal_info(
        stats={
            "wisdom": {"base": 1, "insight": 2},
            "dexterity": 3,
        }
    )
    pc = PlayerCharacter(user="222", character_info=info)
    text = pc.info()
    assert "Test" in text
    assert "222" in text
    assert "Wisdom" in text
    assert "Dexterity" in text


def test_resolve_stat_name_exact_match():
    pc = PlayerCharacter(character_info=_minimal_info())
    assert pc.resolve_stat_name("strength") == ("strength", "stats__strength")


def test_resolve_stat_name_partial_unique():
    pc = PlayerCharacter(character_info=_minimal_info())
    assert pc.resolve_stat_name("stre") == ("strength", "stats__strength")


def test_resolve_stat_name_is_case_insensitive_for_character_sheet_keys():
    pc = PlayerCharacter(character_info=_minimal_info(stats={"Strength": 2}))
    assert pc.resolve_stat_name("str") == ("Strength", "stats__Strength")


def test_resolve_stat_name_ambiguous_returns_false():
    info = _minimal_info(stats={"strength": 1, "stealth": 1})
    pc = PlayerCharacter(character_info=info)
    assert pc.resolve_stat_name("st") is False


def test_get_and_set_stat_nested():
    info = _minimal_info(
        stats={"charisma": {"base": 2, "deception": 3}},
    )
    pc = PlayerCharacter(character_info=info)
    assert pc.get_stat("stats__charisma__deception") == 3
    pc.set_stat("stats__charisma__deception", 5)
    assert pc.character_info["stats"]["charisma"]["deception"] == 5


def test_get_gold_set_gold_get_attack_get_name():
    pc = PlayerCharacter(character_info=_minimal_info())
    assert pc.get_gold() == 50
    pc.set_gold(99)
    assert pc.get_gold() == 99
    assert pc.get_attack() == 2
    assert pc.get_name() == "Test"


def test_change_user():
    pc = PlayerCharacter(user="1", character_info=_minimal_info())
    pc.change_user("2")
    assert pc.user == "2"


def test_validate_character_delegates_to_schema():
    r = validate_character(_minimal_info())
    assert r["status"] is True
