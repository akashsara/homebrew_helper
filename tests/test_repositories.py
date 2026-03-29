from unittest.mock import MagicMock, patch

from homebrew_helper.utils.repositories import HomebrewRepository


def test_raw_db_exposes_database():
    db = MagicMock()
    repo = HomebrewRepository(db)
    assert repo.raw_db is db


def test_save_character_delegates_to_set_details():
    db = MagicMock()
    db["characters"].replace_one.return_value = MagicMock(
        modified_count=1, upserted_id=None, raw_result={}
    )
    repo = HomebrewRepository(db)
    doc = {"character_id": "x", "character_info": {}}
    assert repo.save_character("x", doc) is True
    db["characters"].replace_one.assert_called_once()


def test_get_user_and_save_user():
    db = MagicMock()
    db["users"].find_one.return_value = {"user": "u1"}
    repo = HomebrewRepository(db)
    assert repo.get_user("srv", "u1")["user"] == "u1"
    db["users"].replace_one.return_value = MagicMock(
        modified_count=1, upserted_id=None, raw_result={}
    )
    assert repo.save_user("srv", "u1", {"user": "u1"}) is True


def test_set_alias():
    db = MagicMock()
    db["aliases"].replace_one.return_value = MagicMock(
        modified_count=1, upserted_id=None, raw_result={}
    )
    repo = HomebrewRepository(db)
    assert repo.set_alias("a1", "o1") is True


@patch(
    "homebrew_helper.utils.repositories.database.transfer_characters",
    return_value=True,
)
def test_transfer_user_characters_delegates(mock_tc):
    db = MagicMock()
    repo = HomebrewRepository(db)
    assert repo.transfer_user_characters("s", "a", "b") is True
    mock_tc.assert_called_once_with("s", "a", "b", db)


def test_transfer_gold_between_characters_amount_not_positive():
    db = MagicMock()
    repo = HomebrewRepository(db)
    assert repo.transfer_gold_between_characters("a", "b", 0) is False
    assert repo.transfer_gold_between_characters("a", "b", -1) is False


def test_transfer_gold_between_characters_success():
    db = MagicMock()
    db["characters"].find_one_and_update.return_value = {"character_id": "src"}
    db["characters"].update_one.return_value = MagicMock(matched_count=1)
    repo = HomebrewRepository(db)
    assert repo.transfer_gold_between_characters("src", "dst", 10) is True


def test_transfer_gold_between_characters_insufficient_gold():
    db = MagicMock()
    db["characters"].find_one_and_update.return_value = None
    repo = HomebrewRepository(db)
    assert repo.transfer_gold_between_characters("src", "dst", 10) is False


def test_transfer_gold_between_characters_rolls_back_when_target_missing():
    db = MagicMock()
    db["characters"].find_one_and_update.return_value = {"character_id": "src"}
    db["characters"].update_one.return_value = MagicMock(matched_count=0)
    repo = HomebrewRepository(db)
    assert repo.transfer_gold_between_characters("src", "dst", 5) is False
    assert db["characters"].update_one.call_count >= 2
