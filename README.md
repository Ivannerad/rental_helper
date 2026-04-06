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
