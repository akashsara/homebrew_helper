from discord.ext import commands


class CooldownCogMixin:
    """
    Shared per-user cooldown for every command in a cog. Mix in before
    `commands.Cog` and call `_init_cooldown` from `__init__`.

    Ref: https://stackoverflow.com/questions/65595213/how-to-add-shared-cooldown-to-multiple-discord-py-commands
    """

    def _init_cooldown(self, n_messages: int, cooldown_seconds: int) -> None:
        self._cooldown = commands.CooldownMapping.from_cooldown(
            n_messages, cooldown_seconds, commands.BucketType.user
        )

    async def cog_check(self, context) -> bool:
        # Don't use a cooldown with the help command.
        if context.invoked_with == "help":
            return True
        bucket = self._cooldown.get_bucket(context.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            await context.send(
                f"<@{context.author.id}>: Stop spamming! Please wait {round(retry_after, 2)} seconds to use the command."
            )
            return False
        return True
