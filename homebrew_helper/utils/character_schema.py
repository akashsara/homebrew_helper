from __future__ import annotations

from typing import Dict, Union

from pydantic import BaseModel, ConfigDict, ValidationError

StatEntry = Union[int, Dict[str, int]]


class CharacterInfoPayload(BaseModel):
    """Validated shape for `character_info` stored on a character document."""

    model_config = ConfigDict(extra="ignore")

    name: str
    hp: int = 0
    attack: int
    armor_class: int
    speed: int
    level: int
    gold: int
    stats: Dict[str, StatEntry]


def validate_character_payload(chara: dict) -> Dict[str, Union[bool, str]]:
    try:
        CharacterInfoPayload.model_validate(chara)
        return {"status": True, "error": "None"}
    except ValidationError as e:
        err = e.errors()[0] if e.errors() else {}
        loc = ".".join(str(x) for x in err.get("loc", ()))
        msg = err.get("msg", "validation error")
        detail = f"{loc}: {msg}" if loc else msg
        return {"status": False, "error": detail}
