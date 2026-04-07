# Persistence Migrations

Task 5 introduces SQL-based PostgreSQL migrations under `src/shared/persistence/migrations/`.

## Prerequisites

- PostgreSQL 14+ running locally
- `POSTGRES_DSN` set to a writable database
- project dependencies installed (`python -m pip install -e '.[dev]'`)
- a dedicated local database or schema for validation, because `reset` drops the
  migration-managed tables before recreating them

## Commands

Apply pending migrations:

```bash
python -m shared.persistence.migrator up
```

Rollback the latest migration:

```bash
python -m shared.persistence.migrator down
```

Recreate schema from scratch:

```bash
python -m shared.persistence.migrator reset
```

## Local Validation Flow

1. Set `POSTGRES_DSN` to a local test database.
2. Run `python -m shared.persistence.migrator reset`.
3. Run `python -m pytest tests/shared/persistence/test_migrator.py`.
   The test suite creates a temporary schema per test so it does not reuse or wipe
   unrelated tables in the same database.
4. Confirm core tables exist (`managed_accounts`, `bound_groups`, `conversations`, `listings`, `listing_offers`, `viewing_appointments`, `queue_events`, `account_audit_logs`).
