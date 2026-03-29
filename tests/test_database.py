from unittest.mock import MagicMock

import pytest

from homebrew_helper.utils import database


def test_get_details_returns_document_when_found():
    db = MagicMock()
    doc = {"character_id": "c1"}
    db["characters"].find_one.return_value = doc
    assert database.get_details({"character_id": "c1"}, "characters", db) == doc


def test_get_details_returns_empty_when_missing():
    db = MagicMock()
    db["users"].find_one.return_value = None
    assert database.get_details({"user": "u1"}, "users", db) == {}


def test_set_details_true_on_success():
    db = MagicMock()
    result = MagicMock()
    result.modified_count = 1
    result.upserted_id = None
    result.raw_result = {}
    db["users"].replace_one.return_value = result
    assert database.set_details({"user": "u1"}, {"user": "u1"}, "users", db) is True


def test_set_details_logs_when_no_modification_and_no_upsert():
    db = MagicMock()
    result = MagicMock()
    result.modified_count = 0
    result.upserted_id = None
    result.raw_result = {"n": 0}
    db["users"].replace_one.return_value = result
    assert database.set_details({"user": "u1"}, {"user": "u1"}, "users", db) is True


def test_set_details_false_on_exception():
    db = MagicMock()
    db["users"].replace_one.side_effect = RuntimeError("db down")
    assert database.set_details({"user": "u1"}, {}, "users", db) is False


def test_load_all_characters_indexed_by_id():
    db = MagicMock()
    db["characters"].find.return_value = [
        {"character_id": "a", "x": 1},
        {"character_id": "b", "x": 2},
    ]
    out = database.load_all_characters(db)
    assert out == {
        "a": {"character_id": "a", "x": 1},
        "b": {"character_id": "b", "x": 2},
    }


def test_hydrate_character_models_builds_player_instances():
    db = MagicMock()
    db["characters"].find.return_value = [
        {
            "character_id": "c1",
            "user": "u1",
            "character_info": {
                "name": "Zed",
                "hp": 1,
                "attack": 1,
                "armor_class": 10,
                "speed": 30,
                "level": 1,
                "gold": 0,
                "stats": {},
            },
        }
    ]
    chars = database.hydrate_character_models(db)
    assert "c1" in chars
    assert chars["c1"].get_name() == "Zed"


def test_load_all_users_groups_by_server():
    db = MagicMock()
    db["users"].find.return_value = [
        {"server": "s1", "user": "u1", "active": None, "characters": []},
        {"server": "s1", "user": "u2", "active": None, "characters": []},
    ]
    out = database.load_all_users(db)
    assert "s1" in out
    assert out["s1"]["u1"]["user"] == "u1"
    assert out["s1"]["u2"]["user"] == "u2"


def test_transfer_characters_moves_character_user_and_clears_source():
    db = MagicMock()

    source_doc = {"server": "srv", "user": "a", "characters": ["c1"], "active": "c1"}
    target_doc = {"server": "srv", "user": "b", "characters": [], "active": None}
    char_doc = {
        "character_id": "c1",
        "user": "a",
        "character_info": {
            "name": "N",
            "hp": 1,
            "attack": 1,
            "armor_class": 10,
            "speed": 30,
            "level": 1,
            "gold": 0,
            "stats": {},
        },
    }

    def find_one(query):
        q = dict(query)
        if q == {"server": "srv", "user": "a"}:
            return source_doc.copy()
        if q == {"server": "srv", "user": "b"}:
            return target_doc.copy()
        if q == {"character_id": "c1"}:
            return char_doc.copy()
        return None

    db["users"].find_one.side_effect = find_one
    db["characters"].find_one.side_effect = find_one

    assert database.transfer_characters("srv", "a", "b", db) is True
    assert db["characters"].replace_one.call_count >= 1
    assert db["users"].replace_one.call_count >= 2


def test_transfer_characters_false_without_source_characters():
    db = MagicMock()
    db["users"].find_one.return_value = {"server": "s", "user": "a"}
    assert database.transfer_characters("s", "a", "b", db) is False


def test_transfer_characters_creates_target_without_characters_key():
    db = MagicMock()
    source_doc = {
        "server": "srv",
        "user": "a",
        "characters": ["c1"],
        "active": None,
    }
    char_doc = {
        "character_id": "c1",
        "user": "a",
        "character_info": {
            "name": "N",
            "hp": 1,
            "attack": 1,
            "armor_class": 10,
            "speed": 30,
            "level": 1,
            "gold": 0,
            "stats": {},
        },
    }

    def find_one(query):
        q = dict(query)
        if q == {"server": "srv", "user": "a"}:
            return dict(source_doc)
        if q == {"server": "srv", "user": "b"}:
            return {"server": "srv", "user": "b"}
        if q == {"character_id": "c1"}:
            return dict(char_doc)
        return None

    db["users"].find_one.side_effect = find_one
    db["characters"].find_one.side_effect = find_one
    assert database.transfer_characters("srv", "a", "b", db) is True


def test_transfer_characters_skips_missing_character_doc():
    db = MagicMock()
    source_doc = {
        "server": "srv",
        "user": "a",
        "characters": ["missing"],
        "active": None,
    }

    def find_one(query):
        q = dict(query)
        if q == {"server": "srv", "user": "a"}:
            return dict(source_doc)
        if q == {"server": "srv", "user": "b"}:
            return {
                "server": "srv",
                "user": "b",
                "characters": [],
                "active": None,
            }
        if q == {"character_id": "missing"}:
            return None
        return None

    db["users"].find_one.side_effect = find_one
    db["characters"].find_one.side_effect = find_one
    assert database.transfer_characters("srv", "a", "b", db) is True


def test_transfer_characters_false_on_exception():
    db = MagicMock()
    db["users"].find_one.side_effect = RuntimeError("network")
    assert database.transfer_characters("srv", "a", "b", db) is False


def test_transfer_characters_creates_target_when_user_missing():
    db = MagicMock()
    source_doc = {
        "server": "srv",
        "user": "a",
        "characters": ["c1"],
        "active": None,
    }
    char_doc = {
        "character_id": "c1",
        "user": "a",
        "character_info": {
            "name": "N",
            "hp": 1,
            "attack": 1,
            "armor_class": 10,
            "speed": 30,
            "level": 1,
            "gold": 0,
            "stats": {},
        },
    }

    def find_one(query):
        q = dict(query)
        if q == {"server": "srv", "user": "a"}:
            return dict(source_doc)
        if q == {"server": "srv", "user": "b"}:
            return None
        if q == {"character_id": "c1"}:
            return dict(char_doc)
        return None

    db["users"].find_one.side_effect = find_one
    db["characters"].find_one.side_effect = find_one
    assert database.transfer_characters("srv", "a", "b", db) is True


def test_transfer_characters_does_not_duplicate_character_id_on_target():
    db = MagicMock()
    source_doc = {
        "server": "srv",
        "user": "a",
        "characters": ["c1"],
        "active": None,
    }
    target_doc = {
        "server": "srv",
        "user": "b",
        "characters": ["c1"],
        "active": None,
    }
    char_doc = {
        "character_id": "c1",
        "user": "a",
        "character_info": {
            "name": "N",
            "hp": 1,
            "attack": 1,
            "armor_class": 10,
            "speed": 30,
            "level": 1,
            "gold": 0,
            "stats": {},
        },
    }

    def find_one(query):
        q = dict(query)
        if q == {"server": "srv", "user": "a"}:
            return dict(source_doc)
        if q == {"server": "srv", "user": "b"}:
            return dict(target_doc)
        if q == {"character_id": "c1"}:
            return dict(char_doc)
        return None

    db["users"].find_one.side_effect = find_one
    db["characters"].find_one.side_effect = find_one
    assert database.transfer_characters("srv", "a", "b", db) is True
    last_target = db["users"].replace_one.call_args_list[-1][0][1]
    assert last_target["characters"].count("c1") == 1
