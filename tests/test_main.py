from unittest.mock import patch

import discord

import homebrew_helper.main as main


@patch("homebrew_helper.main.config.require_config")
@patch("homebrew_helper.main.gen_utils.configure_logging")
@patch("homebrew_helper.main.MongoClient")
@patch("homebrew_helper.main.database.hydrate_character_models", return_value={})
@patch("homebrew_helper.main.load_all_users", return_value={})
@patch("homebrew_helper.main.HomebrewHelper")
def test_run_bot_disables_everyone_and_role_mentions_but_keeps_user_mentions(
    mock_bot_cls,
    mock_load_all_users,
    mock_hydrate,
    mock_mongo_client,
    mock_configure_logging,
    mock_require_config,
):
    # Regression: fun.py commands interpolate a raw, unsanitized user-supplied
    # `target` string into context.send(...) (e.g. `!slap @everyone`). Without an
    # explicit AllowedMentions policy, discord.py's default lets @everyone/@here
    # and role mentions actually ping, turning any of those commands into a
    # mass-ping griefing vector. Direct user mentions must stay allowed since the
    # bot legitimately pings users everywhere (e.g. "<@{user}> doesn't have any
    # characters", and the `target` mention in the fun commands themselves).
    main.run_bot()

    _, kwargs = mock_bot_cls.call_args
    allowed_mentions = kwargs["allowed_mentions"]
    assert isinstance(allowed_mentions, discord.AllowedMentions)
    assert allowed_mentions.everyone is False
    assert allowed_mentions.roles is False
    assert allowed_mentions.users is True

    mock_bot_cls.return_value.run.assert_called_once()
