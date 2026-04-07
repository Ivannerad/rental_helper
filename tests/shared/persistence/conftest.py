"""Shared PostgreSQL fixtures for persistence tests."""

from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from shared.persistence.migrator import apply_reset, load_migrations


def _postgres_dsn() -> str:
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        pytest.skip("POSTGRES_DSN is not set; skipping PostgreSQL persistence tests.")
    return dsn


@pytest.fixture
def connection() -> psycopg.Connection:
    schema_name = f"test_schema_{uuid4().hex}"

    with psycopg.connect(_postgres_dsn()) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
            cursor.execute(
                sql.SQL("SET search_path TO {}, public").format(sql.Identifier(schema_name))
            )
        connection.autocommit = False

        try:
            apply_reset(connection, load_migrations())
            yield connection
        finally:
            connection.rollback()
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema_name))
                )
