from typing import Dict, List, Union

import discord
import src.config as config
import src.utils.database as database
from discord.ext import commands
from discord.ext.commands import Bot, DefaultHelpCommand
from pymongo import MongoClient
from src.templates import *
from src.utils import gen_utils
from src.utils.player_character import PlayerCharacter


class HomebrewHelper(Bot):
    def __init__(
        self,
        *args,
        initial_extensions: List[str],
        character_cache: dict,
        user_cache: dict,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.initial_extensions = initial_extensions
        self.character_cache = character_cache
        self.user_cache = user_cache
        self.logger = gen_utils.create_logger("bot")

    def get_current_chara(self, server_id, user_id):
        return self.user_cache.get(server_id, {}).get(user_id, {}).get("active")

    async def setup_hook(self):
        self.logger.info("Loading extensions.")
        for extension in self.initial_extensions:
            self.logger.info(f"Loading Extension: {extension}")
            await self.load_extension(extension)


def load_all_characters() -> Dict[str, Dict[str, Union[str, int]]]:
    """
    Returns a dictionary of all the characters in the database.
    Keys are character IDs and values are that character's information.
    Character IDs for users can be found in the user table.
    """
    with MongoClient(config.DB_TOKEN) as db:
        character_information = database.load_all_characters(db[config.DB_NAME])
    characters = {}
    for character_id, character_data in character_information.items():
        character = PlayerCharacter()
        character.import_stats(character_data)
        characters[character_id] = character
    return characters


def load_all_users() -> Dict[str, Dict[str, Dict[str, Union[str, List[str]]]]]:
    """
    Returns a dictionary of dictionaries for all the users in the database.
    Top level keys are server IDs and the corresponding dictionaries have
    user IDs as the key and the user's info including their active character
    and list of characters as the value.
    {server_id: {character_id: user_info}}
    """
    with MongoClient(config.DB_TOKEN) as db:
        users = database.load_all_users(db[config.DB_NAME])
    return users


def run_bot():
    logger = gen_utils.create_logger(__name__)
    # Load and cache character DB
    # WARNING: This is not built to scale
    logger.info("Loading DnData.")
    character_cache = load_all_characters()
    user_cache = load_all_users()

    # List of cogs we use
    initial_extensions = [
        "src.cogs.fun",
        "src.cogs.rng.dice",
        "src.cogs.rpg.characters",
    ]

    # Create help command
    help_command = DefaultHelpCommand(no_category="Commands")

    # Set intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    # Initialize the bot client
    client = HomebrewHelper(
        command_prefix=config.BOT_PREFIX,
        help_command=help_command,
        intents=intents,
        initial_extensions=initial_extensions,
        character_cache=character_cache,
        user_cache=user_cache,
    )

    # Register event handlers
    @client.event
    async def on_ready():
        await client.change_presence(activity=discord.Game("with fate."))

    @client.event
    async def on_command_error(context, error):
        """Handles command errors with custom messages based on the error type."""
        error_handlers = {
            commands.MissingRequiredArgument: ERROR_MISSING_ARGUMENTS.format(
                user=context.author.id
            ),
            commands.MissingPermissions: ERROR_MISSING_PERMISSIONS.format(
                user=context.author.id
            ),
            commands.CommandInvokeError: ERROR_COMMAND_INVOKE.format(
                user=context.author.id
            ),
            commands.CommandNotFound: ERROR_COMMAND_NOT_FOUND.format(
                user=context.author.id
            ),
        }
        if type(error) in error_handlers:
            logger.warning(f"{type(error).__name__}: {error}")
            await context.send(error_handlers.get(type(error)))
        else:
            logger.error(f"Unhandled command error: {error}")
            raise error

    logger.info("Running client..")
    client.run(config.TOKEN)
