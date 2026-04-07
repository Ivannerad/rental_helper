# File Map

Use this file to find the right part of the repository before scanning broadly.

## Source code

- `src/admin_bot/`: admin Telegram bot
- `src/userbot_worker/`: Telethon worker logic
- `src/chatbot_service/`: chatbot orchestration
- `src/shared/domain/`: shared business models
- `src/shared/config/`: environment and runtime configuration
- `src/shared/persistence/`: migrations and persistence helpers
- `src/shared/queue/`: queue contracts
- `src/shared/logging/`: shared logging

## Tests

- `tests/shared/`: shared package tests
- `tests/admin_bot/`: admin bot tests
- `tests/userbot_worker/`: worker tests
- `tests/chatbot_service/`: chatbot service tests

## Documentation and planning

- `docs/`: persistent repository documentation
- `tasks/`: implementation task specs
- `AGENTS.md`: repository-specific execution and maintenance rules

## Search minimization rule

- If a task clearly belongs to one package, start with that package and the matching test directory.
- Prefer reading source-of-truth files in `docs/task_context/` before scanning broad directories.
