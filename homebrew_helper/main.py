from typing import Dict, List, Union

import discord
import homebrew_helper.config as config
import homebrew_helper.templates as templates
import homebrew_helper.utils.database as database
from discord.ext import commands
from discord.ext.commands import Bot, DefaultHelpCommand
from pymongo import MongoClient
from pymongo.database import Database

from homebrew_helper.utils import gen_utils
from homebrew_helper.utils.repositories import HomebrewRepository


class HomebrewHelper(Bot):
    def __init__(
        self,
        *args,
        initial_extensions: List[str],
        character_cache: dict,
        user_cache: dict,
        mongo_client: MongoClient,
        mongo_db: Database,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.initial_extensions = initial_extensions
        self.character_cache = character_cache
        self.user_cache = user_cache
        self.mongo_client = mongo_client
        self.mongo_db = mongo_db
        self.repo = HomebrewRepository(mongo_db)
        self.logger = gen_utils.get_logger("bot")

    def get_current_chara(self, server_id, user_id):
        return self.user_cache.get(server_id, {}).get(user_id, {}).get("active")

    async def setup_hook(self):
        self.logger.info("Loading extensions.")
        for extension in self.initial_extensions:
            self.logger.info(f"Loading Extension: {extension}")
            await self.load_extension(extension)


def load_all_users(
    db: Database,
) -> Dict[str, Dict[str, Dict[str, Union[str, List[str]]]]]:
    """
    Returns nested dicts: server_id -> user_id -> user document.
    """
    return database.load_all_users(db)


def run_bot():
    config.require_config()
    gen_utils.configure_logging()
    logger = gen_utils.get_logger(__name__)
    # Load and cache character DB
    # WARNING: This is not built to scale
    logger.info("Loading DnData.")
    mongo_client = MongoClient(config.DB_TOKEN)
    mongo_db = mongo_client[config.DB_NAME]
    character_cache = database.hydrate_character_models(mongo_db)
    user_cache = load_all_users(mongo_db)

    # List of cogs we use
    initial_extensions = [
        "homebrew_helper.cogs.fun",
        "homebrew_helper.cogs.rng.dice",
        "homebrew_helper.cogs.rpg.characters",
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
        mongo_client=mongo_client,
        mongo_db=mongo_db,
    )

    # Register event handlers
    @client.event
    async def on_ready():
        await client.change_presence(activity=discord.Game("with fate."))

    @client.event
    async def on_command_error(context, error):
        """Handles command errors with custom messages based on the error type."""
        inner = getattr(error, "original", None)
        if isinstance(error, commands.CommandOnCooldown) or (
            isinstance(error, commands.CommandInvokeError)
            and isinstance(inner, commands.CommandOnCooldown)
        ):
            exc = (
                error
                if isinstance(error, commands.CommandOnCooldown)
                else inner
            )
            logger.warning("CommandOnCooldown: %s", error)
            await context.send(
                templates.ERROR_COMMAND_ON_COOLDOWN.format(
                    user=context.author.id, seconds=exc.retry_after
                )
            )
            return

        if isinstance(error, commands.BadArgument) or (
            isinstance(error, commands.CommandInvokeError)
            and isinstance(inner, commands.BadArgument)
        ):
            exc = error if isinstance(error, commands.BadArgument) else inner
            logger.warning("BadArgument: %s", error)
            await context.send(
                templates.ERROR_BAD_ARGUMENT.format(
                    user=context.author.id, detail=str(exc)
                )
            )
            return

        error_handlers = {
            commands.MissingRequiredArgument: templates.ERROR_MISSING_ARGUMENTS.format(
                user=context.author.id
            ),
            commands.MissingPermissions: templates.ERROR_MISSING_PERMISSIONS.format(
                user=context.author.id
            ),
            commands.CommandInvokeError: templates.ERROR_COMMAND_INVOKE.format(
                user=context.author.id
            ),
            commands.CommandNotFound: templates.ERROR_COMMAND_NOT_FOUND.format(
                user=context.author.id
            ),
        }
        if type(error) in error_handlers:
            logger.warning("%s: %s", type(error).__name__, error)
            await context.send(error_handlers.get(type(error)))
            return

        if isinstance(error, commands.CheckFailure):
            return

        logger.error("Unhandled command error: %s", error)
        raise error

    logger.info("Running client..")
    client.run(config.TOKEN)
