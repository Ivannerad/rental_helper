"""Tests for SQL migration tooling and schema behavior."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import os
from typing import Iterator
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from shared.persistence.migrator import apply_down, apply_reset, apply_up, load_migrations


def _postgres_dsn() -> str:
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        pytest.skip("POSTGRES_DSN is not set; skipping PostgreSQL migration tests.")
    return dsn


@contextmanager
def _test_connection() -> Iterator[psycopg.Connection]:
    schema_name = f"test_schema_{uuid4().hex}"

    with psycopg.connect(_postgres_dsn()) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name))
            )
            cursor.execute(
                sql.SQL("SET search_path TO {}, public").format(
                    sql.Identifier(schema_name)
                )
            )
        connection.autocommit = False

        try:
            yield connection
        finally:
            connection.rollback()
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA {} CASCADE").format(
                        sql.Identifier(schema_name)
                    )
                )


def test_load_migrations_includes_initial_schema() -> None:
    migrations = load_migrations()
    assert migrations
    assert migrations[0].version == "0001_initial_schema"
    assert "CREATE TABLE IF NOT EXISTS managed_accounts" in migrations[0].up_sql


def test_apply_up_is_idempotent_and_apply_down_removes_tables() -> None:
    migrations = load_migrations()

    with _test_connection() as connection:
        assert apply_up(connection, migrations) == ["0001_initial_schema"]
        assert apply_up(connection, migrations) == []

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regclass(current_schema() || '.managed_accounts')"
            )
            assert cursor.fetchone()[0] == "managed_accounts"

            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            assert [row[0] for row in cursor.fetchall()] == ["0001_initial_schema"]

        assert apply_down(connection, migrations, steps=1) == ["0001_initial_schema"]

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regclass(current_schema() || '.managed_accounts')"
            )
            assert cursor.fetchone()[0] is None

            cursor.execute("SELECT COUNT(*) FROM schema_migrations")
            assert cursor.fetchone()[0] == 0


def test_apply_reset_creates_schema_and_supports_basic_persistence() -> None:
    migrations = load_migrations()

    account_id = uuid4()
    group_id = uuid4()
    conversation_id = uuid4()
    listing_id = uuid4()
    offer_id = uuid4()
    appointment_id = uuid4()
    queue_event_id = uuid4()
    audit_id = uuid4()
    now = datetime.now(timezone.utc)

    with _test_connection() as connection:
        apply_reset(connection, migrations)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regclass(current_schema() || '.managed_accounts')"
            )
            assert cursor.fetchone()[0] == "managed_accounts"

            cursor.execute(
                """
                INSERT INTO managed_accounts (id, telegram_phone, display_name, status, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (account_id, "+12025550123", "Primary", "active", now),
            )
            cursor.execute(
                """
                INSERT INTO bound_groups (
                    id, managed_account_id, telegram_group_id, telegram_group_title, bound_at
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (group_id, account_id, -100123456789, "City Rentals", now),
            )
            cursor.execute(
                """
                INSERT INTO conversations (
                    id, managed_account_id, telegram_user_id, stage, status, district,
                    room_count, max_budget, handoff_to_human, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    conversation_id,
                    account_id,
                    9001,
                    "collecting",
                    "open",
                    "west",
                    2,
                    130000,
                    False,
                    now,
                    now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO listings (
                    id, managed_account_id, bound_group_id, group_message_id, district,
                    room_count, price, summary, status, indexed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    listing_id,
                    account_id,
                    group_id,
                    123,
                    "west",
                    2,
                    120000,
                    "2-room flat near metro",
                    "active",
                    now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO listing_offers (id, conversation_id, listing_id, offered_at, rejected)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (offer_id, conversation_id, listing_id, now, False),
            )
            cursor.execute(
                """
                INSERT INTO viewing_appointments (
                    id, managed_account_id, conversation_id, listing_id, telegram_user_id,
                    starts_at, ends_at, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    appointment_id,
                    account_id,
                    conversation_id,
                    listing_id,
                    9001,
                    now,
                    now + timedelta(hours=1),
                    "pending",
                    now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO queue_events (
                    id, direction, queue_name, event_type, managed_account_id, conversation_id,
                    telegram_user_id, correlation_id, idempotency_key, payload, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    queue_event_id,
                    "inbound",
                    "chatbot.inbound",
                    "telegram_message",
                    account_id,
                    conversation_id,
                    9001,
                    "corr-1",
                    "event-1",
                    '{"text":"hi"}',
                    "received",
                ),
            )
            cursor.execute(
                """
                INSERT INTO account_audit_logs (
                    id, managed_account_id, actor_telegram_user_id, action, details
                ) VALUES (%s, %s, %s, %s, %s::jsonb)
                """,
                (audit_id, account_id, 1001, "account_started", '{"source":"admin_bot"}'),
            )

            cursor.execute("SAVEPOINT duplicate_offer_check")
            with pytest.raises(psycopg.errors.UniqueViolation):
                cursor.execute(
                    """
                    INSERT INTO listing_offers (id, conversation_id, listing_id, offered_at, rejected)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (uuid4(), conversation_id, listing_id, now, True),
                )
            cursor.execute("ROLLBACK TO SAVEPOINT duplicate_offer_check")
            cursor.execute("SELECT COUNT(*) FROM managed_accounts")
            assert cursor.fetchone()[0] == 1


def test_queue_events_keep_account_trace_when_conversation_is_deleted() -> None:
    migrations = load_migrations()
    now = datetime.now(timezone.utc)
    account_id = uuid4()
    conversation_id = uuid4()
    queue_event_id = uuid4()

    with _test_connection() as connection:
        apply_reset(connection, migrations)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO managed_accounts (id, telegram_phone, display_name, status, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (account_id, "+12025550126", "Traceable Account", "active", now),
            )
            cursor.execute(
                """
                INSERT INTO conversations (
                    id, managed_account_id, telegram_user_id, stage, status, district,
                    room_count, max_budget, handoff_to_human, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    conversation_id,
                    account_id,
                    880001,
                    "collecting",
                    "open",
                    "west",
                    2,
                    140000,
                    False,
                    now,
                    now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO queue_events (
                    id, direction, queue_name, event_type, managed_account_id, conversation_id,
                    telegram_user_id, payload, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    queue_event_id,
                    "inbound",
                    "chatbot.inbound",
                    "telegram_message",
                    account_id,
                    conversation_id,
                    880001,
                    '{"text":"trace me"}',
                    "received",
                ),
            )

            cursor.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
            cursor.execute(
                """
                SELECT managed_account_id, conversation_id
                FROM queue_events
                WHERE id = %s
                """,
                (queue_event_id,),
            )
            persisted_account_id, persisted_conversation_id = cursor.fetchone()
            assert persisted_account_id == account_id
            assert persisted_conversation_id is None


def test_schema_rejects_cross_account_relationships() -> None:
    migrations = load_migrations()
    now = datetime.now(timezone.utc)

    account_a = uuid4()
    account_b = uuid4()
    group_a = uuid4()
    conversation_a = uuid4()
    listing_a = uuid4()

    with _test_connection() as connection:
        apply_reset(connection, migrations)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO managed_accounts (id, telegram_phone, display_name, status, created_at)
                VALUES (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s)
                """,
                (
                    account_a,
                    "+12025550124",
                    "Account A",
                    "active",
                    now,
                    account_b,
                    "+12025550125",
                    "Account B",
                    "active",
                    now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO bound_groups (
                    id, managed_account_id, telegram_group_id, telegram_group_title, bound_at
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (group_a, account_a, -100100000001, "Group A", now),
            )
            cursor.execute(
                """
                INSERT INTO conversations (
                    id, managed_account_id, telegram_user_id, stage, status, district,
                    room_count, max_budget, handoff_to_human, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    conversation_a,
                    account_a,
                    777001,
                    "collecting",
                    "open",
                    "west",
                    2,
                    130000,
                    False,
                    now,
                    now,
                ),
            )

            cursor.execute("SAVEPOINT cross_account_listing_check")
            with pytest.raises(psycopg.errors.ForeignKeyViolation):
                cursor.execute(
                    """
                    INSERT INTO listings (
                        id, managed_account_id, bound_group_id, group_message_id, district,
                        room_count, price, summary, status, indexed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(),
                        account_b,
                        group_a,
                        5001,
                        "west",
                        2,
                        150000,
                        "cross-account listing",
                        "active",
                        now,
                    ),
                )
            cursor.execute("ROLLBACK TO SAVEPOINT cross_account_listing_check")

            cursor.execute(
                """
                INSERT INTO listings (
                    id, managed_account_id, bound_group_id, group_message_id, district,
                    room_count, price, summary, status, indexed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    listing_a,
                    account_a,
                    group_a,
                    5002,
                    "west",
                    2,
                    150000,
                    "correct account listing",
                    "active",
                    now,
                ),
            )

            cursor.execute("SAVEPOINT cross_account_queue_event_check")
            with pytest.raises(psycopg.errors.CheckViolation):
                cursor.execute(
                    """
                    INSERT INTO queue_events (
                        id, direction, queue_name, event_type, conversation_id, payload, status
                    ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                    """,
                    (
                        uuid4(),
                        "inbound",
                        "chatbot.inbound",
                        "telegram_message",
                        conversation_a,
                        '{"text":"missing account context"}',
                        "received",
                    ),
                )
            cursor.execute("ROLLBACK TO SAVEPOINT cross_account_queue_event_check")

            cursor.execute("SAVEPOINT cross_account_appointment_check")
            with pytest.raises(psycopg.errors.ForeignKeyViolation):
                cursor.execute(
                    """
                    INSERT INTO viewing_appointments (
                        id, managed_account_id, conversation_id, listing_id, telegram_user_id,
                        starts_at, ends_at, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(),
                        account_b,
                        conversation_a,
                        listing_a,
                        777001,
                        now,
                        now + timedelta(hours=1),
                        "pending",
                        now,
                    ),
                )
            cursor.execute("ROLLBACK TO SAVEPOINT cross_account_appointment_check")
