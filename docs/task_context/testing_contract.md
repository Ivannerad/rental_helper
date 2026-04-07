# Testing Contract

This repository uses `pytest` for automated tests.

## Test layout

- Tests mirror the `src/` package split.
- Shared package tests belong under `tests/shared/`.
- Service-specific tests belong under the matching service directory.

## Current commands

- `python -m pytest`
- `python -m ruff check .`
- `python -m ruff format . --check`

## Persistence test rules

- PostgreSQL-backed tests should use `psycopg`.
- Tests that require `POSTGRES_DSN` should skip cleanly when it is not set.
- Migration and persistence tests should prefer isolated schemas rather than reusing shared tables.

## Search minimization rule

- Start with the test directory that matches the package being changed.
- Avoid scanning unrelated tests unless a failure or shared fixture dependency requires it.
