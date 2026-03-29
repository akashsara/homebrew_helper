import importlib

import pytest


def test_require_config_exits_when_token_missing(monkeypatch):
    # Empty values are treated as missing; set explicitly so reload picks them up
    # even when a .env file would otherwise supply tokens (dotenv does not override).
    monkeypatch.setenv("HOMEBREW_HELPER_TOKEN", "")
    monkeypatch.setenv("DATABASE_TOKEN", "")
    import homebrew_helper.config as cfg

    importlib.reload(cfg)
    with pytest.raises(SystemExit):
        cfg.require_config()


def test_require_config_ok_when_tokens_set(monkeypatch):
    monkeypatch.setenv("HOMEBREW_HELPER_TOKEN", "fake-token")
    monkeypatch.setenv("DATABASE_TOKEN", "mongodb://localhost")
    import homebrew_helper.config as cfg

    importlib.reload(cfg)
    cfg.require_config()
