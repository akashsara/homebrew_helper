from __future__ import annotations

from typing import Any, Dict

import pymongo.database

from homebrew_helper.utils import database


class HomebrewRepository:
    """Single entry point for Mongo writes used by cogs (besides bulk loaders)."""

    def __init__(self, db: pymongo.database.Database) -> None:
        self._db = db

    @property
    def raw_db(self) -> pymongo.database.Database:
        return self._db

    def save_character(self, character_id: str, document: Dict[str, Any]) -> bool:
        return database.set_details(
            {"character_id": character_id}, document, "characters", self._db
        )

    def delete_character(self, character_id: str) -> bool:
        return database.delete_details(
            {"character_id": character_id}, "characters", self._db
        )

    def get_user(self, server_id: str, user_id: str) -> Dict[str, Any]:
        return database.get_details(
            {"server": server_id, "user": user_id}, "users", self._db
        )

    def save_user(self, server_id: str, user_id: str, document: Dict[str, Any]) -> bool:
        return database.set_details(
            {"server": server_id, "user": user_id}, document, "users", self._db
        )

    def set_alias(self, alias_id: str, original_id: str) -> bool:
        return database.set_details(
            {"alias": alias_id},
            {"alias": alias_id, "original": original_id},
            "aliases",
            self._db,
        )

    def transfer_user_characters(
        self, server_id: str, source_user: str, target_user: str
    ) -> bool:
        """Move all character documents and user rows from source to target Discord user."""
        return database.transfer_characters(
            server_id, source_user, target_user, self._db
        )

    def transfer_gold_between_characters(
        self, source_character_id: str, target_character_id: str, amount: int
    ) -> bool:
        """
        Decrement source gold only if balance is sufficient, then credit target.
        If crediting target fails, rolls back the source decrement.
        For full ACID across both, use a replica set and a transaction.
        """
        if amount <= 0:
            return False
        res = self._db["characters"].find_one_and_update(
            {
                "character_id": source_character_id,
                "character_info.gold": {"$gte": amount},
            },
            {"$inc": {"character_info.gold": -amount}},
        )
        if res is None:
            return False
        result = self._db["characters"].update_one(
            {"character_id": target_character_id},
            {"$inc": {"character_info.gold": amount}},
        )
        if result.matched_count == 0:
            self._db["characters"].update_one(
                {"character_id": source_character_id},
                {"$inc": {"character_info.gold": amount}},
            )
            return False
        return True
