import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from homebrew_helper.cogs._cooldown import CooldownCogMixin


class _Cog(CooldownCogMixin):
    def __init__(self, n_messages, cooldown_seconds):
        self._init_cooldown(n_messages, cooldown_seconds)


def _context(invoked_with="somecommand", user_id=1):
    author = SimpleNamespace(id=user_id)
    return SimpleNamespace(
        invoked_with=invoked_with,
        author=author,
        message=SimpleNamespace(author=author),
        send=AsyncMock(),
    )


def test_cog_check_allows_first_call_then_blocks_within_window():
    cog = _Cog(n_messages=1, cooldown_seconds=100)
    context = _context()

    assert asyncio.run(cog.cog_check(context)) is True
    assert asyncio.run(cog.cog_check(context)) is False
    context.send.assert_awaited_once()


def test_cog_check_tracks_cooldown_per_user():
    cog = _Cog(n_messages=1, cooldown_seconds=100)
    first_user = _context(user_id=1)
    second_user = _context(user_id=2)

    assert asyncio.run(cog.cog_check(first_user)) is True
    assert asyncio.run(cog.cog_check(second_user)) is True
    first_user.send.assert_not_awaited()
    second_user.send.assert_not_awaited()


def test_cog_check_always_allows_help():
    cog = _Cog(n_messages=1, cooldown_seconds=100)
    context = _context(invoked_with="help")

    assert asyncio.run(cog.cog_check(context)) is True
    assert asyncio.run(cog.cog_check(context)) is True
    context.send.assert_not_awaited()
