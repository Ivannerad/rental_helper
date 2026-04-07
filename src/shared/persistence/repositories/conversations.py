"""Repository for conversation persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from shared.domain import (
    Conversation,
    ConversationStage,
    ConversationStatus,
    LeadRequirements,
)

from ._base import BaseRepository, Session
from ._mappers import CONVERSATION_COLUMNS, conversation_from_row


class ConversationRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def create_conversation(self, conversation: Conversation) -> Conversation:
        row = self._fetch_one(
            f"""
            INSERT INTO conversations ({CONVERSATION_COLUMNS})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {CONVERSATION_COLUMNS}
            """,
            (
                conversation.id,
                conversation.managed_account_id,
                conversation.telegram_user_id,
                conversation.stage.value,
                conversation.status.value,
                conversation.requirements.district,
                conversation.requirements.room_count,
                conversation.requirements.max_budget,
                conversation.handoff_to_human,
                conversation.created_at,
                conversation.updated_at,
            ),
        )
        assert row is not None
        return conversation_from_row(tuple(row))

    def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        row = self._fetch_one(
            f"""
            SELECT {CONVERSATION_COLUMNS}
            FROM conversations
            WHERE id = %s
            """,
            (conversation_id,),
        )
        return None if row is None else conversation_from_row(tuple(row))

    def get_conversation_by_id(self, conversation_id: UUID) -> Conversation | None:
        return self.get_conversation(conversation_id)

    def get_open_conversation(
        self, managed_account_id: UUID, telegram_user_id: int
    ) -> Conversation | None:
        row = self._fetch_one(
            f"""
            SELECT {CONVERSATION_COLUMNS}
            FROM conversations
            WHERE managed_account_id = %s
              AND telegram_user_id = %s
              AND status = %s
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (managed_account_id, telegram_user_id, ConversationStatus.OPEN.value),
        )
        return None if row is None else conversation_from_row(tuple(row))

    def update_stage(
        self,
        conversation_id: UUID,
        stage: ConversationStage,
        *,
        updated_at: datetime | None = None,
    ) -> Conversation | None:
        return self._update_fields(
            conversation_id,
            {"stage": stage.value},
            updated_at=updated_at,
        )

    def update_status(
        self,
        conversation_id: UUID,
        status: ConversationStatus,
        *,
        updated_at: datetime | None = None,
    ) -> Conversation | None:
        return self._update_fields(
            conversation_id,
            {"status": status.value},
            updated_at=updated_at,
        )

    def update_requirements(
        self,
        conversation_id: UUID,
        requirements: LeadRequirements,
        *,
        updated_at: datetime | None = None,
    ) -> Conversation | None:
        return self._update_fields(
            conversation_id,
            {
                "district": requirements.district,
                "room_count": requirements.room_count,
                "max_budget": requirements.max_budget,
            },
            updated_at=updated_at,
        )

    def set_handoff_to_human(
        self,
        conversation_id: UUID,
        handoff_to_human: bool,
        *,
        updated_at: datetime | None = None,
    ) -> Conversation | None:
        return self._update_fields(
            conversation_id,
            {"handoff_to_human": handoff_to_human},
            updated_at=updated_at,
        )

    def update_handoff_to_human(
        self,
        conversation_id: UUID,
        handoff_to_human: bool,
        *,
        updated_at: datetime | None = None,
    ) -> Conversation | None:
        return self.set_handoff_to_human(
            conversation_id,
            handoff_to_human,
            updated_at=updated_at,
        )

    def update_conversation(
        self,
        conversation_id: UUID,
        *,
        stage: ConversationStage | None = None,
        status: ConversationStatus | None = None,
        requirements: LeadRequirements | None = None,
        handoff_to_human: bool | None = None,
        updated_at: datetime | None = None,
    ) -> Conversation | None:
        fields: dict[str, object] = {}
        if stage is not None:
            fields["stage"] = stage.value
        if status is not None:
            fields["status"] = status.value
        if requirements is not None:
            fields["district"] = requirements.district
            fields["room_count"] = requirements.room_count
            fields["max_budget"] = requirements.max_budget
        if handoff_to_human is not None:
            fields["handoff_to_human"] = handoff_to_human
        if not fields:
            return self.get_conversation(conversation_id)
        return self._update_fields(conversation_id, fields, updated_at=updated_at)

    def _update_fields(
        self,
        conversation_id: UUID,
        fields: dict[str, object],
        *,
        updated_at: datetime | None,
    ) -> Conversation | None:
        timestamp = updated_at or datetime.now(timezone.utc)
        assignments = ", ".join(f"{column} = %s" for column in fields)
        params = [*fields.values(), timestamp, conversation_id]
        row = self._fetch_one(
            f"""
            UPDATE conversations
            SET {assignments},
                updated_at = %s
            WHERE id = %s
            RETURNING {CONVERSATION_COLUMNS}
            """,
            params,
        )
        return None if row is None else conversation_from_row(tuple(row))
