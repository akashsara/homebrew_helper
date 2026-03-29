from unittest.mock import patch

import homebrew_helper.config as config
import homebrew_helper.templates as templates
from homebrew_helper.utils import dice as dice_mod


def test_resolve_operation_subtract_via_roll():
    r = dice_mod.roll_handler("1d20-3")
    assert r["status"] == "OK"
    assert r["modifier"] == -3


def test_roll_handler_compound_expression():
    r = dice_mod.roll_handler("1d6+1d4")
    assert r["status"] == "OK"
    assert len(r["rolls"]) == 2


def test_roll_handler_simple_d20():
    r = dice_mod.roll_handler("1d20")
    assert r["status"] == "OK"
    assert r["total"] == sum(r["rolls"][0][1])
    assert len(r["rolls"][0][1]) == 1


def test_roll_handler_with_modifier():
    r = dice_mod.roll_handler("1d20+5")
    assert r["status"] == "OK"
    assert r["modifier"] == 5


def test_roll_handler_too_high_dice_count():
    over = f"{config.DICE_ROLL_MAX_DICE + 1}d6"
    r = dice_mod.roll_handler(over)
    assert r["status"] == "too high"


def test_roll_handler_too_high_die_size():
    over = f"1d{config.DICE_ROLL_LARGEST_DIE + 1}"
    r = dice_mod.roll_handler(over)
    assert r["status"] == "too high"


def test_roll_handler_invalid_characters():
    r = dice_mod.roll_handler("1d20*2")
    assert r["status"] == "wrong"


def test_roll_wrapper_normal():
    r = dice_mod.roll_wrapper("2d6+3", "123456789", "normal")
    assert r["error"] is False
    assert "total" in r["raw"][0]


def test_roll_wrapper_adv_disadv():
    r = dice_mod.roll_wrapper("1d20", "123456789", "adv_disadv", is_advantage=True)
    assert r["error"] is False
    assert len(r["raw"]) == 2


def test_roll_wrapper_repeat():
    r = dice_mod.roll_wrapper("1d6", "123456789", "repeat", n_repeats="3")
    assert r["error"] is False
    assert len(r["raw"]) == 3


def test_roll_wrapper_invalid_repeat_count():
    r = dice_mod.roll_wrapper("1d6", "123456789", "repeat", n_repeats="0")
    assert r["error"] is True


def test_roll_and_repeat_returns_list_on_success():
    out = dice_mod.roll_and_repeat("1d4", 2)
    assert isinstance(out, list)
    assert len(out) == 2
    assert all(x["status"] == "OK" for x in out)


def test_roll_and_repeat_failure_is_single_item_list():
    out = dice_mod.roll_and_repeat("1d20*2", 2)
    assert isinstance(out, list)
    assert len(out) == 1
    assert out[0]["status"] == "wrong"


def test_roll_wrapper_too_many_dice_for_repeat():
    r = dice_mod.roll_wrapper(
        f"{config.DICE_ROLL_MAX_DICE}d6",
        "999",
        "repeat",
        n_repeats="2",
    )
    assert r["error"] is True
    assert "not gonna roll" in r["message"].lower()


def test_roll_wrapper_invalid_roll_type():
    r = dice_mod.roll_wrapper("1d20", "999", "not_a_mode")
    assert r["error"] is True
    assert templates.ROLL_WRAPPER_INVALID_ROLL_TYPE.format(author_id="999") in r[
        "message"
    ]


def test_roll_wrapper_dice_too_high():
    # Exceeds largest die face (n_dice stays within repeat limit unlike 51d6).
    over = f"1d{config.DICE_ROLL_LARGEST_DIE + 1}"
    r = dice_mod.roll_wrapper(over, "999", "normal")
    assert r["error"] is True
    assert "absurdly high" in r["message"].lower()


def test_roll_wrapper_wrong_dice_command_message():
    r = dice_mod.roll_wrapper("1d20*", "999", "normal")
    assert r["error"] is True
    assert "not how you do it" in r["message"].lower()


def test_roll_wrapper_disadvantage_picks_lower():
    r = dice_mod.roll_wrapper("1d20", "999", "adv_disadv", is_advantage=False)
    assert r["error"] is False
    assert len(r["raw"]) == 2
    assert r["final_result"][0] == min(r["raw"][0]["total"], r["raw"][1]["total"])


def test_dice_roll_formatter_normal_shape():
    results = [
        {
            "user_roll": "1d20",
            "rolls": [("1d20", [10])],
            "modifier": 0,
            "total": 10,
            "status": "OK",
        }
    ]
    out = dice_mod.dice_roll_formatter("1d20", "1", "normal", results, [10])
    assert "<@1>" in out or "@1" in out


def test_roll_dice_and_parse_roll_modifier_only_segment():
    r = dice_mod.roll_handler("0d6+5")
    assert r["status"] == "OK"
    assert r["total"] == 5


def test_roll_handler_second_segment_too_high():
    # Trailing +0 forces parsing the absurd pool in the loop (not only at end).
    over = f"1d20+{config.DICE_ROLL_MAX_DICE + 1}d6+0"
    r = dice_mod.roll_handler(over)
    assert r["status"] == "too high"


def test_roll_handler_double_plus_is_wrong():
    r = dice_mod.roll_handler("1d20++5")
    assert r["status"] == "wrong"


@patch("homebrew_helper.utils.dice.roll_and_repeat")
def test_roll_wrapper_unknown_roll_status(mock_repeat):
    mock_repeat.return_value = [{"status": "unexpected"}]
    r = dice_mod.roll_wrapper("1d20", "1", "normal")
    assert r["error"] is True
    assert templates.ROLL_WRAPPER_UNKNOWN_ERROR in r["message"]


def test_dice_roll_formatter_repeat():
    results = [
        {
            "user_roll": "1d6",
            "rolls": [("1d6", [4])],
            "modifier": 0,
            "total": 4,
            "status": "OK",
        },
        {
            "user_roll": "1d6",
            "rolls": [("1d6", [2])],
            "modifier": 0,
            "total": 2,
            "status": "OK",
        },
    ]
    out = dice_mod.dice_roll_formatter("1d6r2", "9", "repeat", results, [4, 2])
    assert "Final Rolls" in out
