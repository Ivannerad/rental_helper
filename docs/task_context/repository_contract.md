# Repository Contract

This file describes repository-wide source-of-truth rules so agents can avoid rediscovering them by scanning large parts of the codebase.

## Current stable contracts

- Shared domain entities live in `src/shared/domain/models.py`.
- Runtime configuration loading lives in `src/shared/config/settings.py`.
- PostgreSQL migration execution lives in `src/shared/persistence/migrator.py`.
- SQL schema source of truth lives in `src/shared/persistence/migrations/`.

## Contract rules

- When a task changes a public shared contract, update the corresponding source-of-truth file and this summary if needed.
- Do not infer public contracts from downstream usage in service packages when the shared source-of-truth file already exists.
- Prefer changing shared contracts intentionally in one place rather than creating ad hoc duplicates in service code.

## Persistence design rules

- Use explicit SQL with `psycopg`.
- Keep transaction ownership explicit.
- Keep row mapping and SQL close together inside `shared.persistence`.
- If a task introduces a new repository API, the task file should define the exact class and method contract instead of requiring discovery from service code.

## Task-authoring rule

When a future task needs more than one or two public interfaces, the task should list the exact source-of-truth files rather than telling the agent to inspect the whole repository.
