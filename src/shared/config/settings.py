"""Typed runtime configuration loading for all services."""

from __future__ import annotations

from dataclasses import dataclass
import os


class ConfigError(ValueError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class TelegramSettings:
    api_id: int
    api_hash: str
    bot_token: str


@dataclass(frozen=True)
class DatabaseSettings:
    dsn: str


@dataclass(frozen=True)
class RabbitMQSettings:
    dsn: str


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    api_key: str
    model: str


@dataclass(frozen=True)
class AdminSettings:
    telegram_user_ids: tuple[int, ...]


@dataclass(frozen=True)
class ServiceSettings:
    chatbot_concurrency: int
    userbot_worker_concurrency: int


@dataclass(frozen=True)
class AppSettings:
    telegram: TelegramSettings
    database: DatabaseSettings
    rabbitmq: RabbitMQSettings
    llm: LLMSettings
    admin: AdminSettings
    service: ServiceSettings


_REQUIRED_KEYS = {
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
    "TELEGRAM_BOT_TOKEN",
    "POSTGRES_DSN",
    "RABBITMQ_DSN",
    "LLM_PROVIDER",
    "LLM_API_KEY",
    "LLM_MODEL",
    "ADMIN_TELEGRAM_USER_IDS",
}


def load_settings(env: dict[str, str] | None = None) -> AppSettings:
    """Load application settings from environment variables."""
    source = env if env is not None else dict(os.environ)

    missing_keys = sorted(key for key in _REQUIRED_KEYS if not source.get(key))
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ConfigError(f"Missing required environment variables: {missing}")

    return AppSettings(
        telegram=TelegramSettings(
            api_id=_read_int(source, "TELEGRAM_API_ID"),
            api_hash=source["TELEGRAM_API_HASH"],
            bot_token=source["TELEGRAM_BOT_TOKEN"],
        ),
        database=DatabaseSettings(dsn=source["POSTGRES_DSN"]),
        rabbitmq=RabbitMQSettings(dsn=source["RABBITMQ_DSN"]),
        llm=LLMSettings(
            provider=source["LLM_PROVIDER"],
            api_key=source["LLM_API_KEY"],
            model=source["LLM_MODEL"],
        ),
        admin=AdminSettings(
            telegram_user_ids=_read_admin_user_ids(source["ADMIN_TELEGRAM_USER_IDS"]),
        ),
        service=ServiceSettings(
            chatbot_concurrency=_read_int(source, "CHATBOT_CONCURRENCY", default=4),
            userbot_worker_concurrency=_read_int(source, "USERBOT_WORKER_CONCURRENCY", default=4),
        ),
    )


def _read_int(source: dict[str, str], key: str, *, default: int | None = None) -> int:
    raw_value = source.get(key)
    if raw_value is None or raw_value == "":
        if default is not None:
            return default
        raise ConfigError(f"Missing required integer environment variable: {key}")

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"Invalid integer for {key}: {raw_value!r}") from exc


def _read_admin_user_ids(raw_value: str) -> tuple[int, ...]:
    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    if not values:
        raise ConfigError("ADMIN_TELEGRAM_USER_IDS must include at least one Telegram user ID")

    parsed_ids: list[int] = []
    for item in values:
        try:
            parsed_ids.append(int(item))
        except ValueError as exc:
            raise ConfigError(
                f"Invalid Telegram user ID in ADMIN_TELEGRAM_USER_IDS: {item!r}"
            ) from exc
    return tuple(parsed_ids)
