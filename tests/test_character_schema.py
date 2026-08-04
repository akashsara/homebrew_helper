from homebrew_helper.utils.character_schema import validate_character_payload


def test_validate_character_payload_ok():
    payload = {
        "name": "Lan",
        "hp": 10,
        "attack": 5,
        "armor_class": 15,
        "speed": 30,
        "level": 3,
        "gold": 100,
        "stats": {"strength": 2, "charisma": {"base": 1, "deception": 3}},
    }
    r = validate_character_payload(payload)
    assert r["status"] is True


def test_validate_character_payload_missing_field():
    r = validate_character_payload({"name": "x"})
    assert r["status"] is False
    assert "error" in r


def test_validate_character_payload_extra_fields_ignored():
    payload = {
        "name": "A",
        "attack": 1,
        "armor_class": 10,
        "speed": 30,
        "level": 1,
        "gold": 0,
        "stats": {},
        "unknown_field": 123,
    }
    r = validate_character_payload(payload)
    assert r["status"] is True
    assert "unknown_field" not in r["data"]


def test_validate_character_payload_defaults_missing_hp():
    # Regression: hp has a schema default, so omitting it must still validate --
    # but callers need the default applied to the returned data, since the raw
    # payload has no "hp" key and would otherwise crash downstream (e.g. PlayerCharacter.info()).
    payload = {
        "name": "A",
        "attack": 1,
        "armor_class": 10,
        "speed": 30,
        "level": 1,
        "gold": 0,
        "stats": {},
    }
    r = validate_character_payload(payload)
    assert r["status"] is True
    assert r["data"]["hp"] == 0


def test_validate_character_payload_wrong_type():
    r = validate_character_payload(
        {
            "name": "A",
            "attack": "nope",
            "armor_class": 10,
            "speed": 30,
            "level": 1,
            "gold": 0,
            "stats": {},
        }
    )
    assert r["status"] is False
    assert "attack" in r["error"]
