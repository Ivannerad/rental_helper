"""Simple SQL migration runner for shared persistence schema."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib.resources import files
import os
from typing import Iterable

import psycopg


MIGRATIONS_PACKAGE = "shared.persistence.migrations"
MIGRATION_TABLE = "schema_migrations"


@dataclass(frozen=True)
class Migration:
    version: str
    up_sql: str
    down_sql: str


def _read_sql(filename: str) -> str:
    return files(MIGRATIONS_PACKAGE).joinpath(filename).read_text(encoding="utf-8")


def load_migrations() -> list[Migration]:
    migration_dir = files(MIGRATIONS_PACKAGE)
    up_files = sorted(
        path.name for path in migration_dir.iterdir() if path.name.endswith(".up.sql")
    )
    migrations: list[Migration] = []
    for up_file in up_files:
        version = up_file.removesuffix(".up.sql")
        down_file = f"{version}.down.sql"
        if not migration_dir.joinpath(down_file).is_file():
            raise ValueError(f"Missing down migration for version {version}")
        migrations.append(
            Migration(
                version=version,
                up_sql=_read_sql(up_file),
                down_sql=_read_sql(down_file),
            )
        )
    return migrations


def _ensure_migration_table(connection: psycopg.Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    connection.commit()


def _applied_versions(connection: psycopg.Connection) -> set[str]:
    _ensure_migration_table(connection)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT version FROM {MIGRATION_TABLE}")
        return {row[0] for row in cursor.fetchall()}


def _execute_script(connection: psycopg.Connection, script: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(script)
    connection.commit()


def apply_up(connection: psycopg.Connection, migrations: Iterable[Migration]) -> list[str]:
    applied = _applied_versions(connection)
    newly_applied: list[str] = []
    for migration in migrations:
        if migration.version in applied:
            continue
        _execute_script(connection, migration.up_sql)
        with connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO {MIGRATION_TABLE} (version) VALUES (%s) ON CONFLICT DO NOTHING",
                (migration.version,),
            )
        connection.commit()
        newly_applied.append(migration.version)
    return newly_applied


def apply_down(
    connection: psycopg.Connection, migrations: Iterable[Migration], steps: int = 1
) -> list[str]:
    if steps < 1:
        raise ValueError("steps must be >= 1")

    applied = _applied_versions(connection)
    applied_ordered = [migration for migration in migrations if migration.version in applied]
    to_rollback = list(reversed(applied_ordered))[:steps]
    rolled_back: list[str] = []
    for migration in to_rollback:
        _execute_script(connection, migration.down_sql)
        with connection.cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {MIGRATION_TABLE} WHERE version = %s", (migration.version,)
            )
        connection.commit()
        rolled_back.append(migration.version)
    return rolled_back


def apply_reset(connection: psycopg.Connection, migrations: Iterable[Migration]) -> None:
    while apply_down(connection, migrations, steps=1):
        pass
    apply_up(connection, migrations)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PostgreSQL schema migrations.")
    parser.add_argument(
        "command", choices=("up", "down", "reset"), help="Migration action to execute."
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="How many migrations to roll back when command is down.",
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("POSTGRES_DSN"),
        help="PostgreSQL DSN. Defaults to POSTGRES_DSN env var.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.dsn:
        raise SystemExit("POSTGRES_DSN is required (set env var or pass --dsn).")

    migrations = load_migrations()
    with psycopg.connect(args.dsn) as connection:
        if args.command == "up":
            applied = apply_up(connection, migrations)
            print(f"Applied migrations: {applied or 'none'}")
        elif args.command == "down":
            rolled_back = apply_down(connection, migrations, steps=args.steps)
            print(f"Rolled back migrations: {rolled_back or 'none'}")
        else:
            apply_reset(connection, migrations)
            print("Schema reset complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
