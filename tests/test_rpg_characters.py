from homebrew_helper.cogs.rpg.characters import (
    RPGCommands,
    _find_owned_character_matches,
    _format_character_matches,
    _format_owned_character_list,
    _is_yes_response,
    _resolve_target_user_id,
    _split_rename_payload,
    _get_owned_characters,
    _normalize_modifiers,
)
from homebrew_helper.utils.player_character import PlayerCharacter
import asyncio
from types import SimpleNamespace
from discord.ext import commands


def _character(character_id: str, name: str, stats=None) -> PlayerCharacter:
    if stats is None:
        stats = {"strength": 2}
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
            "stats": stats,
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


def test_normalize_modifiers_joins_bonus_and_advantage_tokens():
    assert _normalize_modifiers(("+3", "a")) == "+3a"


class _FakeContext:
    def __init__(self):
        self.author = SimpleNamespace(id="111")
        self.guild = SimpleNamespace(id="guild")
        self.sent = []
        self.invocations = []

    async def send(self, message):
        self.sent.append(message)

    async def invoke(self, command, *args):
        self.invocations.append((command, args))


class _FakeBot:
    def __init__(self, stats=None):
        self.character_cache = {"c1": _character("c1", "Ayla", stats=stats)}
        self.roll_command = SimpleNamespace(name="roll")

    def get_current_chara(self, server, user_id):
        return "c1"

    def get_command(self, name):
        if name == "roll":
            return self.roll_command
        return None


def test_saving_throw_accepts_separate_bonus_and_advantage_tokens():
    cog = RPGCommands(_FakeBot())
    context = _FakeContext()

    asyncio.run(cog.saving_throw.callback(cog, context, "str", "+3", "a"))

    assert context.sent == ["Rolling for Strength."]
    assert context.invocations == [(cog.bot.roll_command, ("1d20+2+3a",))]


def test_saving_throw_resolves_capitalized_stat_keys():
    cog = RPGCommands(_FakeBot(stats={"Strength": 2}))
    context = _FakeContext()

    asyncio.run(cog.saving_throw.callback(cog, context, "str", "+3", "a"))

    assert context.sent == ["Rolling for Strength."]
    assert context.invocations == [(cog.bot.roll_command, ("1d20+2+3a",))]


def test_saving_throw_invalid_stat_sends_message_instead_of_raising():
    cog = RPGCommands(_FakeBot())
    context = _FakeContext()

    asyncio.run(cog.saving_throw.callback(cog, context, "notastat", "+3", "a"))

    assert context.sent == ["Hey <@111>, that doesn't seem like a valid stat."]
    assert context.invocations == []


def test_attack_accepts_separate_bonus_and_advantage_tokens():
    cog = RPGCommands(_FakeBot())
    context = _FakeContext()

    asyncio.run(cog.attack.callback(cog, context, "+3", "a"))

    assert context.invocations == [(cog.bot.roll_command, ("1d20+2+3a",))]


def test_rpg_command_help_messages_do_not_use_placeholders():
    command_helps = [
        command.help
        for _, command in vars(RPGCommands).items()
        if isinstance(command, commands.Command)
    ]

    assert command_helps
    assert all(help_text and "coming soon" not in help_text.lower() for help_text in command_helps)


def test_rpg_commands_use_short_primary_names_and_keep_legacy_aliases():
    commands_by_attr = {
        attr: command
        for attr, command in vars(RPGCommands).items()
        if isinstance(command, commands.Command)
    }

    assert commands_by_attr["create_character"].name == "create"
    assert "create_character" in commands_by_attr["create_character"].aliases

    assert commands_by_attr["list_characters"].name == "chars"
    assert "list_characters" in commands_by_attr["list_characters"].aliases

    assert commands_by_attr["rename_character"].name == "rename"
    assert "rename_character" in commands_by_attr["rename_character"].aliases

    assert commands_by_attr["switch_character"].name == "switch"
    assert "switch_character" in commands_by_attr["switch_character"].aliases

    assert commands_by_attr["delete_character"].name == "delete"
    assert "delete_character" in commands_by_attr["delete_character"].aliases

    assert commands_by_attr["change_stat"].name == "setstat"
    assert "change_stat" in commands_by_attr["change_stat"].aliases

    assert commands_by_attr["add_alias"].name == "alias"
    assert "add_alias" in commands_by_attr["add_alias"].aliases

    assert commands_by_attr["get_current_gold"].name == "gold"
    assert "get_current_gold" in commands_by_attr["get_current_gold"].aliases

    assert commands_by_attr["change_gold"].name == "goldadd"
    assert "change_gold" in commands_by_attr["change_gold"].aliases

    assert commands_by_attr["set_gold"].name == "goldset"
    assert "set_gold" in commands_by_attr["set_gold"].aliases

    assert commands_by_attr["transfer_gold"].name == "pay"
    assert "transfer_gold" in commands_by_attr["transfer_gold"].aliases
