# Architecture Schema

This repository is a service-oriented Python monorepo under `src/`.

## Package boundaries

- `src/admin_bot/`: Telegram admin bot logic
- `src/userbot_worker/`: Telethon user session workers
- `src/chatbot_service/`: chatbot orchestration and business-flow logic
- `src/shared/domain/`: shared business entities and enums
- `src/shared/persistence/`: PostgreSQL migrations and persistence helpers
- `src/shared/config/`: environment-driven configuration loading
- `src/shared/queue/`: message transport contracts and helpers
- `src/shared/logging/`: shared logging setup

## Dependency rules

- Service packages may import `shared.domain`, `shared.persistence`, `shared.config`, `shared.queue`, and `shared.logging`.
- `shared.*` packages must not import service packages.
- Importable application code belongs under `src/`.
- Operational docs belong under `docs/`.
- Automated tests mirror the package split under `tests/`.

## Extension points

- Shared domain entities should be added under `src/shared/domain/`.
- Database migrations should be added under `src/shared/persistence/migrations/`.
- New cross-service infrastructure code belongs under `src/shared/`.
- One-off developer utilities belong under `scripts/`.

## Persistence guidance

- Use `psycopg` 3 for PostgreSQL access.
- Prefer explicit SQL and explicit transaction boundaries.
- Keep row-to-domain mapping in the persistence layer.
- Do not introduce an ORM unless a task explicitly authorizes that change.
