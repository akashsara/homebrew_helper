import logging
from typing import Dict

import pymongo

logger = logging.getLogger(__name__)


def get_details(query: Dict, collection: str, db: pymongo.database.Database) -> Dict:
    """
    query: to select exactly one item from the DB
    collection: the table from our DB
    db: MongoDB database cursor
    """
    details = db[collection].find_one(query)
    if details:
        return details
    logger.info(f"Could not find information for query {query}")
    return {}


def set_details(
    query: Dict, payload: Dict, collection: str, db: pymongo.database.Database
) -> bool:
    """
    query: to select exactly one item from the DB
    payload: to store in the DB
    collection: the table in our DB
    db: MongoDB database cursor
    """
    try:
        result = db[collection].replace_one(query, payload, upsert=True)
        if result.modified_count == 0 and not result.upserted_id:
            logger.info(f"Unknown error occured.\n{result.raw_result}")
        return True
    except Exception as e:
        logger.info(f"Exception in set_details: {e}")
        return False


def load_all_characters(db: pymongo.database.Database):
    """
    db: MongoDB database cursor
    """
    all_characters = db["characters"].find({})
    return {char["character_id"]: char for char in all_characters}


def hydrate_character_models(db: pymongo.database.Database):
    """Load all character documents as PlayerCharacter instances (startup / full resync)."""
    from homebrew_helper.utils.player_character import PlayerCharacter

    characters = {}
    for character_id, character_data in load_all_characters(db).items():
        character = PlayerCharacter()
        character.import_stats(character_data)
        characters[character_id] = character
    return characters


def load_all_users(db: pymongo.database.Database):
    """
    db: MongoDB database cursor

    Users:
    {
        "_id": "unique_id",
        "server": "discord_server_id",
        "user": "discord_user_id",
        "active": "currently_active_character_id",
        "characters": ["list", "of", "character_ids"]
    }
    """
    result = db["users"].find({})
    all_users = {}
    for user in result:
        if user["server"] in all_users:
            all_users[user["server"]][user["user"]] = user
        else:
            all_users[user["server"]] = {user["user"]: user}
    return all_users


def transfer_characters(
    server_id: str, source_user: str, target_user: str, db: pymongo.database.Database
):
    """
    server_id: Discord server function was called on
    source_user: User to transfer characters from (Discord snowflake string)
    target_user: User to transfer characters to (Discord snowflake string)
    db: MongoDB database cursor
    """
    try:
        source_query = {"server": server_id, "user": source_user}
        source = get_details(source_query, "users", db)
        target_query = {"server": server_id, "user": target_user}
        target = get_details(target_query, "users", db)
        if not source or "characters" not in source:
            logger.info("transfer_characters: missing source user or characters list")
            return False
        if not target:
            target = {
                "server": server_id,
                "user": target_user,
                "characters": [],
                "active": None,
            }
        if "characters" not in target:
            target["characters"] = []
        for character_id in source["characters"]:
            query = {"character_id": character_id}
            character = get_details(query, "characters", db)
            if not character:
                logger.info(
                    "transfer_characters: character %s not found", character_id
                )
                continue
            character["user"] = target_user
            set_details(query, character, "characters", db)
            if character_id not in target["characters"]:
                target["characters"].append(character_id)
        source["characters"] = []
        set_details(source_query, source, "users", db)
        set_details(target_query, target, "users", db)
        return True
    except Exception as e:
        logger.info(f"Exception in transfer_characters: {e}")
        return False
