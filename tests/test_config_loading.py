"""Tests for shared configuration loading."""

from __future__ import annotations

import pytest

from shared.config import ConfigError, load_settings


def _valid_env() -> dict[str, str]:
    return {
        "TELEGRAM_API_ID": "123456",
        "TELEGRAM_API_HASH": "api_hash",
        "TELEGRAM_BOT_TOKEN": "bot-token",
        "POSTGRES_DSN": "postgresql://user:pass@localhost:5432/rental",
        "RABBITMQ_DSN": "amqp://guest:guest@localhost:5672/",
        "LLM_PROVIDER": "openai",
        "LLM_API_KEY": "secret-key",
        "LLM_MODEL": "gpt-4.1-mini",
        "ADMIN_TELEGRAM_USER_IDS": "1001,1002",
    }


def test_load_settings_parses_required_and_optional_values() -> None:
    settings = load_settings(_valid_env())

    assert settings.telegram.api_id == 123456
    assert settings.admin.telegram_user_ids == (1001, 1002)
    assert settings.service.chatbot_concurrency == 4
    assert settings.service.userbot_worker_concurrency == 4


def test_load_settings_accepts_concurrency_overrides() -> None:
    env = _valid_env()
    env["CHATBOT_CONCURRENCY"] = "7"
    env["USERBOT_WORKER_CONCURRENCY"] = "2"

    settings = load_settings(env)

    assert settings.service.chatbot_concurrency == 7
    assert settings.service.userbot_worker_concurrency == 2


def test_load_settings_fails_when_required_value_is_missing() -> None:
    env = _valid_env()
    del env["RABBITMQ_DSN"]

    with pytest.raises(ConfigError, match="RABBITMQ_DSN"):
        load_settings(env)


def test_load_settings_fails_when_admin_ids_are_invalid() -> None:
    env = _valid_env()
    env["ADMIN_TELEGRAM_USER_IDS"] = "1001,not-a-number"

    with pytest.raises(ConfigError, match="ADMIN_TELEGRAM_USER_IDS"):
        load_settings(env)
