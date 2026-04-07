"""Repositories for managed accounts and bound groups."""

from __future__ import annotations

from uuid import UUID

from shared.domain import AccountStatus, BoundGroup, ManagedAccount

from ._base import BaseRepository, Session
from ._mappers import (
    BOUND_GROUP_COLUMNS,
    MANAGED_ACCOUNT_COLUMNS,
    bound_group_from_row,
    managed_account_from_row,
)


class AccountRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def create_account(self, account: ManagedAccount) -> ManagedAccount:
        row = self._fetch_one(
            f"""
            INSERT INTO managed_accounts ({MANAGED_ACCOUNT_COLUMNS})
            VALUES (%s, %s, %s, %s, %s)
            RETURNING {MANAGED_ACCOUNT_COLUMNS}
            """,
            (
                account.id,
                account.telegram_phone,
                account.display_name,
                account.status.value,
                account.created_at,
            ),
        )
        assert row is not None
        return managed_account_from_row(tuple(row))

    def get_account(self, account_id: UUID) -> ManagedAccount | None:
        row = self._fetch_one(
            f"""
            SELECT {MANAGED_ACCOUNT_COLUMNS}
            FROM managed_accounts
            WHERE id = %s
            """,
            (account_id,),
        )
        return None if row is None else managed_account_from_row(tuple(row))

    def get_account_by_id(self, account_id: UUID) -> ManagedAccount | None:
        return self.get_account(account_id)

    def get_account_by_phone(self, telegram_phone: str) -> ManagedAccount | None:
        row = self._fetch_one(
            f"""
            SELECT {MANAGED_ACCOUNT_COLUMNS}
            FROM managed_accounts
            WHERE telegram_phone = %s
            """,
            (telegram_phone,),
        )
        return None if row is None else managed_account_from_row(tuple(row))

    def update_account_status(
        self, account_id: UUID, status: AccountStatus
    ) -> ManagedAccount | None:
        row = self._fetch_one(
            f"""
            UPDATE managed_accounts
            SET status = %s
            WHERE id = %s
            RETURNING {MANAGED_ACCOUNT_COLUMNS}
            """,
            (status.value, account_id),
        )
        return None if row is None else managed_account_from_row(tuple(row))

    def upsert_bound_group(self, bound_group: BoundGroup) -> BoundGroup:
        row = self._fetch_one(
            f"""
            INSERT INTO bound_groups ({BOUND_GROUP_COLUMNS})
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (managed_account_id) DO UPDATE
            SET telegram_group_id = EXCLUDED.telegram_group_id,
                telegram_group_title = EXCLUDED.telegram_group_title,
                bound_at = EXCLUDED.bound_at
            RETURNING {BOUND_GROUP_COLUMNS}
            """,
            (
                bound_group.id,
                bound_group.managed_account_id,
                bound_group.telegram_group_id,
                bound_group.telegram_group_title,
                bound_group.bound_at,
            ),
        )
        assert row is not None
        return bound_group_from_row(tuple(row))

    def attach_bound_group(self, bound_group: BoundGroup) -> BoundGroup:
        return self.upsert_bound_group(bound_group)

    def get_bound_group_for_account(self, managed_account_id: UUID) -> BoundGroup | None:
        row = self._fetch_one(
            f"""
            SELECT {BOUND_GROUP_COLUMNS}
            FROM bound_groups
            WHERE managed_account_id = %s
            """,
            (managed_account_id,),
        )
        return None if row is None else bound_group_from_row(tuple(row))
