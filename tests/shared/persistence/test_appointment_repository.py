"""Tests for viewing appointment repository behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from shared.domain import (
    AccountStatus,
    AppointmentStatus,
    BoundGroup,
    Conversation,
    ConversationStage,
    ConversationStatus,
    LeadRequirements,
    Listing,
    ListingStatus,
    ManagedAccount,
    ViewingAppointment,
)
from shared.persistence import AccountRepository, AppointmentRepository, ListingRepository
from shared.persistence.repositories import ConversationRepository


def test_appointment_repository_orders_conversation_and_upcoming_queries(connection) -> None:
    account_repository = AccountRepository(connection)
    conversation_repository = ConversationRepository(connection)
    listing_repository = ListingRepository(connection)
    appointment_repository = AppointmentRepository(connection)
    now = datetime.now(timezone.utc)
    account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550180",
            display_name="Appointment Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    other_account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550181",
            display_name="Other Appointment Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    group = account_repository.upsert_bound_group(
        BoundGroup(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_group_id=-100400000001,
            telegram_group_title="Appointments Feed",
            bound_at=now,
        )
    )
    other_group = account_repository.upsert_bound_group(
        BoundGroup(
            id=uuid4(),
            managed_account_id=other_account.id,
            telegram_group_id=-100400000002,
            telegram_group_title="Other Feed",
            bound_at=now,
        )
    )
    conversation = conversation_repository.create_conversation(
        Conversation(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_user_id=6010,
            stage=ConversationStage.VIEWING,
            status=ConversationStatus.OPEN,
            requirements=LeadRequirements(district="west", room_count=2, max_budget=130000),
            handoff_to_human=False,
            created_at=now,
            updated_at=now,
        )
    )
    other_conversation = conversation_repository.create_conversation(
        Conversation(
            id=uuid4(),
            managed_account_id=other_account.id,
            telegram_user_id=6011,
            stage=ConversationStage.VIEWING,
            status=ConversationStatus.OPEN,
            requirements=LeadRequirements(),
            handoff_to_human=False,
            created_at=now,
            updated_at=now,
        )
    )
    listing = listing_repository.upsert_listing(
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=401,
            district="west",
            room_count=2,
            price=120000,
            summary="Viewing candidate",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        )
    )
    other_listing = listing_repository.upsert_listing(
        Listing(
            id=uuid4(),
            managed_account_id=other_account.id,
            bound_group_id=other_group.id,
            group_message_id=402,
            district="east",
            room_count=1,
            price=90000,
            summary="Other viewing candidate",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        )
    )
    appointments = [
        ViewingAppointment(
            id=uuid4(),
            managed_account_id=account.id,
            conversation_id=conversation.id,
            listing_id=listing.id,
            telegram_user_id=conversation.telegram_user_id,
            starts_at=now + timedelta(hours=3),
            ends_at=now + timedelta(hours=4),
            status=AppointmentStatus.PENDING,
            created_at=now,
        ),
        ViewingAppointment(
            id=uuid4(),
            managed_account_id=account.id,
            conversation_id=conversation.id,
            listing_id=listing.id,
            telegram_user_id=conversation.telegram_user_id,
            starts_at=now - timedelta(hours=3),
            ends_at=now - timedelta(hours=2),
            status=AppointmentStatus.COMPLETED,
            created_at=now,
        ),
        ViewingAppointment(
            id=uuid4(),
            managed_account_id=account.id,
            conversation_id=conversation.id,
            listing_id=listing.id,
            telegram_user_id=conversation.telegram_user_id,
            starts_at=now + timedelta(hours=1),
            ends_at=now + timedelta(hours=2),
            status=AppointmentStatus.CONFIRMED,
            created_at=now,
        ),
    ]
    other_account_appointment = ViewingAppointment(
        id=uuid4(),
        managed_account_id=other_account.id,
        conversation_id=other_conversation.id,
        listing_id=other_listing.id,
        telegram_user_id=other_conversation.telegram_user_id,
        starts_at=now + timedelta(minutes=30),
        ends_at=now + timedelta(hours=1, minutes=30),
        status=AppointmentStatus.PENDING,
        created_at=now,
    )

    for appointment in appointments:
        appointment_repository.create_appointment(appointment)
    appointment_repository.create_appointment(other_account_appointment)

    by_conversation = appointment_repository.list_by_conversation(conversation.id)
    upcoming = appointment_repository.list_upcoming_for_account(account.id, starts_from=now)

    assert [appointment.id for appointment in by_conversation] == [
        appointments[1].id,
        appointments[2].id,
        appointments[0].id,
    ]
    assert [appointment.id for appointment in upcoming] == [
        appointments[2].id,
        appointments[0].id,
    ]


def test_appointment_repository_updates_status(connection) -> None:
    account_repository = AccountRepository(connection)
    conversation_repository = ConversationRepository(connection)
    listing_repository = ListingRepository(connection)
    appointment_repository = AppointmentRepository(connection)
    now = datetime.now(timezone.utc)
    account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550182",
            display_name="Status Appointment Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    group = account_repository.upsert_bound_group(
        BoundGroup(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_group_id=-100400000003,
            telegram_group_title="Status Feed",
            bound_at=now,
        )
    )
    conversation = conversation_repository.create_conversation(
        Conversation(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_user_id=6020,
            stage=ConversationStage.VIEWING,
            status=ConversationStatus.OPEN,
            requirements=LeadRequirements(),
            handoff_to_human=False,
            created_at=now,
            updated_at=now,
        )
    )
    listing = listing_repository.upsert_listing(
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=403,
            district="west",
            room_count=2,
            price=125000,
            summary="Status candidate",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        )
    )
    appointment = appointment_repository.create_appointment(
        ViewingAppointment(
            id=uuid4(),
            managed_account_id=account.id,
            conversation_id=conversation.id,
            listing_id=listing.id,
            telegram_user_id=conversation.telegram_user_id,
            starts_at=now + timedelta(hours=1),
            ends_at=now + timedelta(hours=2),
            status=AppointmentStatus.PENDING,
            created_at=now,
        )
    )

    updated = appointment_repository.update_status(appointment.id, AppointmentStatus.CONFIRMED)

    assert updated is not None
    assert updated.status is AppointmentStatus.CONFIRMED
    assert appointment_repository.list_by_conversation(conversation.id) == [updated]
