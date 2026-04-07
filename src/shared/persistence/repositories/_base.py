"""Shared repository primitives."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from psycopg import Connection, Cursor

Session = Connection[Any] | Cursor[Any]
Row = Sequence[Any]


class BaseRepository:
    """Small helper around a connection or transaction-scoped cursor."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _fetch_one(self, query: str, params: Sequence[Any] = ()) -> Row | None:
        return self._session.execute(query, params).fetchone()

    def _fetch_all(self, query: str, params: Sequence[Any] = ()) -> list[Row]:
        return self._session.execute(query, params).fetchall()
