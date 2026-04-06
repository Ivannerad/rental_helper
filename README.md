# rental_helper

Python monorepo scaffold for a Telegram rental assistant.

## Repository layout

```text
src/
  admin_bot/
  userbot_worker/
  chatbot_service/
  shared/
    config/
    domain/
    logging/
    persistence/
    queue/
tests/
  admin_bot/
  userbot_worker/
  chatbot_service/
  shared/
    config/
    domain/
    logging/
    persistence/
    queue/
```

All importable code belongs under `src/`. Tests are organized by the same service/shared split under `tests/`.

## Local development commands

### Install

```bash
python -m pip install -e '.[dev]'
```

### Lint

```bash
python -m ruff check .
```

### Format check

```bash
python -m ruff format . --check
```

### Test

```bash
python -m pytest
```

## Example environment variables

```bash
export TELEGRAM_API_ID=123456
export TELEGRAM_API_HASH="your-telegram-api-hash"
export TELEGRAM_BOT_TOKEN="123456:telegram-bot-token"
export POSTGRES_DSN="postgresql://user:pass@localhost:5432/rental_helper"
export RABBITMQ_DSN="amqp://guest:guest@localhost:5672/"
export LLM_PROVIDER="openai"
export LLM_API_KEY="sk-..."
export LLM_MODEL="gpt-4.1-mini"
export ADMIN_TELEGRAM_USER_IDS="111111111,222222222"
# Optional concurrency knobs
export CHATBOT_CONCURRENCY=4
export USERBOT_WORKER_CONCURRENCY=4
```

Never commit real secrets or production credentials.
