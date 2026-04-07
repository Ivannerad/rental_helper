"""Tests for conversation repository behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from shared.domain import (
    AccountStatus,
    Conversation,
    ConversationStage,
    ConversationStatus,
    LeadRequirements,
    ManagedAccount,
)
from shared.persistence import AccountRepository
from shared.persistence.repositories import ConversationRepository


def test_conversation_repository_maps_requirements_to_and_from_columns(connection) -> None:
    account_repository = AccountRepository(connection)
    conversation_repository = ConversationRepository(connection)
    now = datetime.now(timezone.utc)
    account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550160",
            display_name="Conversation Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    conversation = Conversation(
        id=uuid4(),
        managed_account_id=account.id,
        telegram_user_id=4001,
        stage=ConversationStage.COLLECTING,
        status=ConversationStatus.OPEN,
        requirements=LeadRequirements(district="west", room_count=2, max_budget=130000),
        handoff_to_human=False,
        created_at=now,
        updated_at=now,
    )

    created = conversation_repository.create_conversation(conversation)
    fetched = conversation_repository.get_conversation(conversation.id)

    assert created == conversation
    assert fetched == conversation

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT district, room_count, max_budget
            FROM conversations
            WHERE id = %s
            """,
            (conversation.id,),
        )
        assert cursor.fetchone() == ("west", 2, 130000)


def test_conversation_repository_updates_state_requirements_and_handoff(connection) -> None:
    account_repository = AccountRepository(connection)
    conversation_repository = ConversationRepository(connection)
    now = datetime.now(timezone.utc)
    account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550161",
            display_name="Stateful Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    conversation = conversation_repository.create_conversation(
        Conversation(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_user_id=4002,
            stage=ConversationStage.COLLECTING,
            status=ConversationStatus.OPEN,
            requirements=LeadRequirements(district="west", room_count=1, max_budget=90000),
            handoff_to_human=False,
            created_at=now,
            updated_at=now,
        )
    )

    stage_updated_at = now + timedelta(minutes=1)
    status_updated_at = now + timedelta(minutes=2)
    requirements_updated_at = now + timedelta(minutes=3)
    handoff_updated_at = now + timedelta(minutes=4)

    stage_updated = conversation_repository.update_stage(
        conversation.id,
        ConversationStage.SEARCHING,
        updated_at=stage_updated_at,
    )
    status_updated = conversation_repository.update_status(
        conversation.id,
        ConversationStatus.PAUSED,
        updated_at=status_updated_at,
    )
    requirements_updated = conversation_repository.update_requirements(
        conversation.id,
        LeadRequirements(district="central", room_count=2, max_budget=110000),
        updated_at=requirements_updated_at,
    )
    handoff_updated = conversation_repository.update_handoff_to_human(
        conversation.id,
        True,
        updated_at=handoff_updated_at,
    )

    assert stage_updated is not None
    assert stage_updated.stage is ConversationStage.SEARCHING
    assert stage_updated.updated_at == stage_updated_at
    assert status_updated is not None
    assert status_updated.status is ConversationStatus.PAUSED
    assert status_updated.updated_at == status_updated_at
    assert requirements_updated is not None
    assert requirements_updated.requirements == LeadRequirements(
        district="central",
        room_count=2,
        max_budget=110000,
    )
    assert requirements_updated.updated_at == requirements_updated_at
    assert handoff_updated is not None
    assert handoff_updated.handoff_to_human is True
    assert handoff_updated.updated_at == handoff_updated_at
    assert (
        conversation_repository.get_open_conversation(account.id, conversation.telegram_user_id)
        is None
    )


def test_conversation_repository_finds_latest_open_conversation_for_user(connection) -> None:
    account_repository = AccountRepository(connection)
    conversation_repository = ConversationRepository(connection)
    now = datetime.now(timezone.utc)
    account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550162",
            display_name="Lookup Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    closed = conversation_repository.create_conversation(
        Conversation(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_user_id=4999,
            stage=ConversationStage.COLLECTING,
            status=ConversationStatus.CLOSED,
            requirements=LeadRequirements(),
            handoff_to_human=False,
            created_at=now,
            updated_at=now,
        )
    )
    open_conversation = conversation_repository.create_conversation(
        Conversation(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_user_id=4999,
            stage=ConversationStage.SEARCHING,
            status=ConversationStatus.OPEN,
            requirements=LeadRequirements(district="west"),
            handoff_to_human=False,
            created_at=now + timedelta(minutes=1),
            updated_at=now + timedelta(minutes=1),
        )
    )

    assert closed.status is ConversationStatus.CLOSED
    assert (
        conversation_repository.get_open_conversation(
            account.id, open_conversation.telegram_user_id
        )
        == open_conversation
    )
