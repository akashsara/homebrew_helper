import logging
import uuid
from unittest.mock import patch

import pytest

from homebrew_helper.utils import gen_utils


def test_configure_logging_idempotent_second_call_only_adjusts_level():
    logging.getLogger().handlers.clear()
    gen_utils.configure_logging(logging.WARNING)
    assert logging.getLogger().level == logging.WARNING
    gen_utils.configure_logging(logging.DEBUG)
    assert logging.getLogger().level == logging.DEBUG


def test_get_logger_returns_named_logger():
    log = gen_utils.get_logger("test.module")
    assert log.name == "test.module"


def test_generate_id_is_uuid_string():
    s = gen_utils.generate_id()
    assert isinstance(s, str)
    uuid.UUID(s)


def test_generate_unique_id_returns_when_not_in_set():
    seen = {"existing"}
    with patch.object(gen_utils, "generate_id", side_effect=["new-id", "other"]):
        assert gen_utils.generate_unique_id(seen) == "new-id"
        assert "new-id" not in seen  # function does not mutate set


def test_generate_unique_id_retries_on_collision():
    seen = {"a", "b"}
    with patch.object(
        gen_utils,
        "generate_id",
        side_effect=["a", "b", "fresh"],
    ):
        assert gen_utils.generate_unique_id(seen) == "fresh"


def test_generate_unique_id_raises_after_max_retries():
    with patch.object(gen_utils, "generate_id", return_value="same"):
        with pytest.raises(RuntimeError, match="Unable to generate unique ID"):
            gen_utils.generate_unique_id({"same"})


def test_get_default_user_shape():
    u = gen_utils.get_default_user()
    assert u == {"active": None, "characters": []}


def test_discord_name_to_id_extracts_snowflake():
    assert gen_utils.discord_name_to_id("<@!123456789012345678>") == "123456789012345678"


def test_discord_name_to_id_none_when_no_digits():
    assert gen_utils.discord_name_to_id("no-id-here") is None


def test_format_stat():
    assert gen_utils.format_stat("armor_class") == "Armor Class"


def test_pad_left_and_right():
    assert gen_utils.pad("7", 3, "left") == "  7"
    assert gen_utils.pad("7", 3, "right") == "7  "


def test_format_rolls_single_group():
    rolls = [("1d20", [15])]
    out = gen_utils.format_rolls(rolls)
    assert "1d20" in out
    assert "15" in out


def test_format_repeated_rolls():
    results = [
        {
            "user_roll": "1d6",
            "rolls": [("1d6", [3])],
            "modifier": 0,
            "total": 3,
        }
    ]
    out = gen_utils.format_repeated_rolls(results)
    assert "1d6" in out
    assert "3" in out


@pytest.mark.parametrize(
    "modifiers, expected_mod, expected_adv",
    [
        ("", "", ""),
        ("+2", "+2", ""),
        ("2", "+2", ""),
        ("+1a", "+1", "a"),
        ("-3d", "-3", "d"),
    ],
)
def test_parse_modifiers(modifiers, expected_mod, expected_adv):
    m, adv = gen_utils.parse_modifiers(modifiers)
    assert m == expected_mod
    assert adv == expected_adv
