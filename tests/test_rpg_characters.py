import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext.commands.view import StringView

from homebrew_helper.cogs.rpg.characters import (
    RPGCommands,
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
from discord.ext import commands


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


def test_resolve_target_user_id_does_not_misread_numeric_query_as_admin_target():
    # Regression: character ids are UUIDs (hex, so plausibly digit-led prefixes
    # like "4a2f"). discord_name_to_id would match the leading digits of any such
    # query and misinterpret an admin's own character search as "target user 4".
    # Only an actual <@id> mention should be treated as a target-user override.
    context = SimpleNamespace(
        author=SimpleNamespace(
            id="111",
            guild_permissions=SimpleNamespace(administrator=True),
        )
    )

    target_user_id, query = _resolve_target_user_id(context, "4a2f | New Name")

    assert target_user_id == "111"
    assert query == "4a2f | New Name"


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


def _context(**overrides):
    defaults = dict(
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(id=123),
        send=AsyncMock(),
        invoke=AsyncMock(),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_saving_throw_with_unresolvable_stat_sends_invalid_stat_message():
    # Regression: resolve_stat_name returns None (previously False) when a stat
    # can't be resolved. saving_throw used to unpack that return value as a tuple
    # unconditionally, which raised a TypeError instead of showing INVALID_STAT.
    character = _character("c1", "Ayla")
    bot = SimpleNamespace(
        get_current_chara=lambda server, user_id: "c1",
        character_cache={"c1": character},
    )
    cog = RPGCommands(bot)
    context = _context()

    asyncio.run(RPGCommands.saving_throw.callback(cog, context, "nonexistent_stat"))

    context.invoke.assert_not_awaited()
    context.send.assert_awaited_once()
    assert "valid stat" in context.send.call_args[0][0].lower()


def test_change_stat_with_unresolvable_stat_sends_invalid_stat_message():
    character = _character("c1", "Ayla")
    bot = SimpleNamespace(
        get_current_chara=lambda server, user_id: "c1",
        character_cache={"c1": character},
        repo=MagicMock(),
    )
    cog = RPGCommands(bot)
    context = _context()

    asyncio.run(
        RPGCommands.change_stat.callback(cog, context, "123", "nonexistent_stat", "5")
    )

    bot.repo.save_character.assert_not_called()
    context.send.assert_awaited_once()
    assert "valid stat" in context.send.call_args[0][0].lower()


async def _dispatch(command, cog, raw_args: str):
    """
    Runs `raw_args` through discord.py's real argument parser (the same
    StringView-based parser the bot uses in production) and then invokes the
    command body with the parsed args/kwargs, exactly like discord.py's own
    invocation path.
    """
    command = command.copy()
    command.cog = cog
    context = SimpleNamespace(
        view=StringView(raw_args),
        message=SimpleNamespace(attachments=[]),
        guild=SimpleNamespace(id=1),
        author=SimpleNamespace(id=999),
        channel=object(),
        send=AsyncMock(),
    )
    await command._parse_arguments(context)
    await command.callback(*context.args, **context.kwargs)
    return context


def test_create_character_preserves_spaces_in_quoted_json_string_values():
    # Regression: create_character used to collect its JSON payload with a
    # variadic `*character_info` parameter and rejoin the tokens with
    # "".join(character_info). Discord.py's argument parser treats `"` as a
    # quoting character, so real JSON (which always starts `{"key":`) either
    # lost the spaces inside quoted string values or, in the common case of a
    # payload like `{"name": "John Doe", ...}`, raised UnexpectedQuoteError
    # before the command body even ran -- an error type the bot's error
    # handler doesn't recognize, so admins got no response at all.
    # `character_info` is now a keyword-only "consume rest" parameter, so
    # discord.py hands it the raw remainder of the message untouched.
    bot = SimpleNamespace(
        character_cache={},
        wait_for=AsyncMock(side_effect=asyncio.TimeoutError),
    )
    cog = RPGCommands(bot)
    raw_args = (
        '<@123> {"name": "John Doe", "attack": 1, "armor_class": 10, '
        '"speed": 30, "level": 1, "gold": 0, "stats": {}}'
    )

    context = asyncio.run(
        _dispatch(RPGCommands.create_character, cog, raw_args)
    )

    sent_messages = [call.args[0] for call in context.send.await_args_list]
    assert any("John Doe" in message for message in sent_messages)


def test_rpg_commands_have_a_shared_cooldown():
    # Regression: unlike FunStuff, RPGCommands previously had no cooldown check
    # at all, so its DB-writing commands (goldadd, create, etc.) could be spammed
    # without limit -- worsened by every write going through blocking pymongo
    # calls on the bot's single event loop.
    cog = RPGCommands(SimpleNamespace(), n_messages=1, cooldown=100)
    author = SimpleNamespace(id=1)
    context = _context(
        invoked_with="gold",
        author=author,
        message=SimpleNamespace(author=author),
    )

    allowed_first = asyncio.run(cog.cog_check(context))
    allowed_second = asyncio.run(cog.cog_check(context))

    assert allowed_first is True
    assert allowed_second is False
    context.send.assert_awaited_once()


@pytest.mark.parametrize(
    "command_name, raw_args",
    [
        ("change_stat", "<@1> strength notanumber"),
        ("change_gold", "<@1> notanumber"),
        ("set_gold", "<@1> notanumber"),
    ],
)
def test_numeric_commands_reject_bad_values_with_bad_argument(command_name, raw_args):
    # Regression: value/amount used to be converted manually via int(value) inside
    # the command body, so a bad value raised a bare ValueError, which main.py's
    # error handler shows as a generic "something went wrong" message -- leaving
    # its dedicated, more helpful BadArgument branch unreachable. Typing these
    # parameters as `int` lets discord.py's own argument parser raise BadArgument
    # directly, which the error handler already knows how to turn into a specific
    # "invalid argument: ..." message.
    cog = RPGCommands(SimpleNamespace())
    command = getattr(RPGCommands, command_name)

    with pytest.raises(commands.BadArgument):
        asyncio.run(_dispatch(command, cog, raw_args))


def test_transfer_gold_rejects_non_integer_amount_with_bad_argument():
    cog = RPGCommands(SimpleNamespace())

    with pytest.raises(commands.BadArgument):
        asyncio.run(_dispatch(RPGCommands.transfer_gold, cog, "notanumber <@1>"))


# Cleanup: goldadd/goldset/setstat/delete/alias mutate persistent game state but
# previously logged nothing, leaving no record of who changed what. Each of these
# verifies the command now emits an audit-trail log line on success.


def test_change_stat_success_logs_audit_entry(caplog):
    character = _character("c1", "Ayla")
    bot = SimpleNamespace(
        get_current_chara=lambda server, user_id: "c1",
        character_cache={"c1": character},
        repo=AsyncMock(),
    )
    cog = RPGCommands(bot)
    context = _context()

    with caplog.at_level(logging.INFO, logger="bot.rpg_commands"):
        asyncio.run(RPGCommands.change_stat.callback(cog, context, "123", "strength", 9))

    assert any("setstat:" in record.message for record in caplog.records)


def test_change_gold_success_logs_audit_entry(caplog):
    character = _character("c1", "Ayla")
    bot = SimpleNamespace(
        get_current_chara=lambda server, user_id: "c1",
        character_cache={"c1": character},
        repo=AsyncMock(),
    )
    cog = RPGCommands(bot)
    context = _context()

    with caplog.at_level(logging.INFO, logger="bot.rpg_commands"):
        asyncio.run(RPGCommands.change_gold.callback(cog, context, "123", 50))

    assert any("goldadd:" in record.message for record in caplog.records)


def test_set_gold_success_logs_audit_entry(caplog):
    character = _character("c1", "Ayla")
    bot = SimpleNamespace(
        get_current_chara=lambda server, user_id: "c1",
        character_cache={"c1": character},
        repo=AsyncMock(),
    )
    cog = RPGCommands(bot)
    context = _context()

    with caplog.at_level(logging.INFO, logger="bot.rpg_commands"):
        asyncio.run(RPGCommands.set_gold.callback(cog, context, "123", 200))

    assert any("goldset:" in record.message for record in caplog.records)


def test_delete_character_success_logs_audit_entry(caplog):
    character = _character("c1", "Ayla")
    author = SimpleNamespace(
        id=111, guild_permissions=SimpleNamespace(administrator=False)
    )
    bot = SimpleNamespace(
        user_cache={"1": {"111": {"characters": ["c1"], "active": "c1"}}},
        character_cache={"c1": character},
        repo=AsyncMock(),
        wait_for=AsyncMock(return_value=SimpleNamespace(content="y")),
    )
    cog = RPGCommands(bot)
    context = _context(author=author, guild=SimpleNamespace(id=1))

    with caplog.at_level(logging.INFO, logger="bot.rpg_commands"):
        asyncio.run(RPGCommands.delete_character.callback(cog, context, query="Ayla"))

    assert any("delete:" in record.message for record in caplog.records)


def test_add_alias_success_logs_audit_entry(caplog, monkeypatch):
    bot = SimpleNamespace(repo=AsyncMock())
    bot.repo.raw_db = MagicMock()
    cog = RPGCommands(bot)
    context = _context(guild=SimpleNamespace(id=1))

    monkeypatch.setattr(
        "homebrew_helper.cogs.rpg.characters.database.load_all_users",
        lambda db: {},
    )
    monkeypatch.setattr(
        "homebrew_helper.cogs.rpg.characters.database.hydrate_character_models",
        lambda db: {},
    )

    with caplog.at_level(logging.INFO, logger="bot.rpg_commands"):
        asyncio.run(RPGCommands.add_alias.callback(cog, context, "<@222>", "<@333>"))

    assert any("alias:" in record.message for record in caplog.records)
