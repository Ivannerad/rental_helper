"""Tests for account and bound-group repositories."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from shared.domain import AccountStatus, BoundGroup, ManagedAccount
from shared.persistence import AccountRepository


def test_account_repository_creates_fetches_and_updates_accounts(connection) -> None:
    repository = AccountRepository(connection)
    created_at = datetime.now(timezone.utc)
    account = ManagedAccount(
        id=uuid4(),
        telegram_phone="+12025550150",
        display_name="Primary Account",
        status=AccountStatus.PENDING,
        created_at=created_at,
    )

    created = repository.create_account(account)
    fetched_by_id = repository.get_account(account.id)
    fetched_by_phone = repository.get_account_by_phone(account.telegram_phone)
    updated = repository.update_account_status(account.id, AccountStatus.ACTIVE)

    assert created == account
    assert fetched_by_id == account
    assert fetched_by_phone == account
    assert updated is not None
    assert updated.status is AccountStatus.ACTIVE
    assert repository.get_account(account.id) == updated


def test_account_repository_attaches_and_replaces_single_bound_group(connection) -> None:
    repository = AccountRepository(connection)
    created_at = datetime.now(timezone.utc)
    account = repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550151",
            display_name="Bound Account",
            status=AccountStatus.ACTIVE,
            created_at=created_at,
        )
    )
    first_group = BoundGroup(
        id=uuid4(),
        managed_account_id=account.id,
        telegram_group_id=-100200000001,
        telegram_group_title="City Rentals",
        bound_at=created_at,
    )
    replacement = BoundGroup(
        id=uuid4(),
        managed_account_id=account.id,
        telegram_group_id=-100200000002,
        telegram_group_title="Updated Rentals",
        bound_at=created_at + timedelta(minutes=5),
    )

    inserted = repository.upsert_bound_group(first_group)
    replaced = repository.upsert_bound_group(replacement)
    fetched = repository.get_bound_group_for_account(account.id)

    assert inserted == first_group
    assert replaced is not None
    assert replaced.id == first_group.id
    assert replaced.telegram_group_id == replacement.telegram_group_id
    assert replaced.telegram_group_title == replacement.telegram_group_title
    assert replaced.bound_at == replacement.bound_at
    assert fetched == replaced

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM bound_groups WHERE managed_account_id = %s",
            (account.id,),
        )
        assert cursor.fetchone()[0] == 1
