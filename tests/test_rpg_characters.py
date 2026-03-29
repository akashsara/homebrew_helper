from homebrew_helper.cogs.rpg.characters import (
    _find_owned_character_matches,
    _format_character_matches,
    _format_owned_character_list,
    _is_yes_response,
    _resolve_target_user_id,
    _split_rename_payload,
    _get_owned_characters,
)
from homebrew_helper.utils.player_character import PlayerCharacter
from types import SimpleNamespace


def _character(character_id: str, name: str) -> PlayerCharacter:
    return PlayerCharacter(
        user="u1",
        character_id=character_id,
        character_info={
            "name": name,
            "hp": 10,
            "attack": 2,
            "armor_class": 14,
            "speed": 30,
            "level": 2,
            "gold": 50,
            "stats": {"strength": 2},
        },
    )


def test_get_owned_characters_returns_present_characters_only():
    user_info = {"characters": ["c1", "missing", "c2"]}
    cache = {"c1": _character("c1", "Ayla"), "c2": _character("c2", "Bran")}

    owned = _get_owned_characters(user_info, cache)

    assert [character.character_id for character in owned] == ["c1", "c2"]


def test_find_owned_character_matches_prefers_exact_name_match():
    user_info = {"characters": ["c1", "c2"]}
    cache = {"c1": _character("c1", "Ayla"), "c2": _character("c2", "Ayla Prime")}

    matches = _find_owned_character_matches(user_info, cache, "Ayla")

    assert [character.character_id for character in matches] == ["c1"]


def test_find_owned_character_matches_prefers_exact_id_match():
    user_info = {"characters": ["c1", "c2"]}
    cache = {"c1": _character("c1", "Ayla"), "c2": _character("c2", "Bran")}

    matches = _find_owned_character_matches(user_info, cache, "c2")

    assert [character.character_id for character in matches] == ["c2"]


def test_find_owned_character_matches_returns_partial_matches():
    user_info = {"characters": ["c1", "c2"]}
    cache = {"c1": _character("c1", "Ayla"), "c2": _character("c2", "Ayla Prime")}

    matches = _find_owned_character_matches(user_info, cache, "ayla")

    assert [character.character_id for character in matches] == ["c1"]


def test_find_owned_character_matches_returns_ambiguous_results():
    user_info = {"characters": ["c1", "c2"]}
    cache = {"c1": _character("c1", "Ayla"), "c2": _character("c2", "Aylar")}

    matches = _find_owned_character_matches(user_info, cache, "ayl")

    assert sorted(character.character_id for character in matches) == ["c1", "c2"]


def test_format_character_matches_includes_name_and_id():
    formatted = _format_character_matches(
        [_character("c1", "Ayla"), _character("c2", "Bran")]
    )

    assert "Ayla (`c1`)" in formatted
    assert "Bran (`c2`)" in formatted


def test_format_owned_character_list_marks_active_character():
    formatted = _format_owned_character_list(
        [_character("c1", "Ayla"), _character("c2", "Bran")],
        "c2",
        "u1",
    )

    assert "2 character(s) for <@u1>:" in formatted
    assert "- Ayla (`c1`)" in formatted
    assert "- Bran (`c2`) [active]" in formatted


def test_split_rename_payload_splits_query_and_new_name():
    query, new_name = _split_rename_payload("Ayla | Ayla Stormborn")

    assert query == "Ayla"
    assert new_name == "Ayla Stormborn"


def test_split_rename_payload_returns_none_without_separator():
    query, new_name = _split_rename_payload("Ayla")

    assert query is None
    assert new_name is None


def test_is_yes_response_accepts_yes_prefix():
    assert _is_yes_response("Y") is True
    assert _is_yes_response(" yes") is True


def test_is_yes_response_rejects_non_yes_prefix():
    assert _is_yes_response("n") is False
    assert _is_yes_response("cancel") is False


def test_resolve_target_user_id_keeps_self_for_regular_user():
    context = SimpleNamespace(
        author=SimpleNamespace(
            id="111",
            guild_permissions=SimpleNamespace(administrator=False),
        )
    )

    target_user_id, query = _resolve_target_user_id(context, "<@222> Ayla")

    assert target_user_id == "111"
    assert query == "<@222> Ayla"


def test_resolve_target_user_id_extracts_admin_target():
    context = SimpleNamespace(
        author=SimpleNamespace(
            id="111",
            guild_permissions=SimpleNamespace(administrator=True),
        )
    )

    target_user_id, query = _resolve_target_user_id(context, "<@222> Ayla Prime")

    assert target_user_id == "222"
    assert query == "Ayla Prime"
