"""Tests for shared domain entities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from shared.domain import (
    AccountStatus,
    AppointmentStatus,
    BoundGroup,
    Conversation,
    ConversationStage,
    ConversationStatus,
    LeadRequirements,
    Listing,
    ListingOffer,
    ListingStatus,
    ManagedAccount,
    ViewingAppointment,
)


def test_domain_entities_can_be_instantiated() -> None:
    now = datetime.now(timezone.utc)
    account_id = uuid4()
    conversation_id = uuid4()
    bound_group_id = uuid4()
    listing_id = uuid4()

    account = ManagedAccount(
        id=account_id,
        telegram_phone="+12025550123",
        display_name="Primary Account",
        status=AccountStatus.ACTIVE,
        created_at=now,
    )
    bound_group = BoundGroup(
        id=bound_group_id,
        managed_account_id=account.id,
        telegram_group_id=-100123456789,
        telegram_group_title="City Rentals",
        bound_at=now,
    )
    requirements = LeadRequirements(district="west", room_count=2, max_budget=130000)
    conversation = Conversation(
        id=conversation_id,
        managed_account_id=account.id,
        telegram_user_id=9001,
        stage=ConversationStage.COLLECTING,
        status=ConversationStatus.OPEN,
        requirements=requirements,
        handoff_to_human=False,
        created_at=now,
        updated_at=now,
    )
    listing = Listing(
        id=listing_id,
        managed_account_id=account.id,
        bound_group_id=bound_group.id,
        group_message_id=123,
        district="west",
        room_count=2,
        price=120000,
        summary="2-room flat near metro",
        status=ListingStatus.ACTIVE,
        indexed_at=now,
    )
    offer = ListingOffer(
        id=uuid4(),
        conversation_id=conversation.id,
        listing_id=listing.id,
        offered_at=now,
    )
    appointment = ViewingAppointment(
        id=uuid4(),
        managed_account_id=account.id,
        conversation_id=conversation.id,
        listing_id=listing.id,
        telegram_user_id=9001,
        starts_at=now,
        ends_at=now + timedelta(hours=1),
        status=AppointmentStatus.PENDING,
        created_at=now,
    )

    assert account.status is AccountStatus.ACTIVE
    assert conversation.stage is ConversationStage.COLLECTING
    assert offer.rejected is False
    assert appointment.status is AppointmentStatus.PENDING


def test_lead_requirements_validate_positive_numbers() -> None:
    with pytest.raises(ValueError, match="room_count"):
        LeadRequirements(room_count=0)

    with pytest.raises(ValueError, match="max_budget"):
        LeadRequirements(max_budget=-1)


def test_listing_validates_positive_numbers() -> None:
    now = datetime.now(timezone.utc)

    with pytest.raises(ValueError, match="room_count"):
        Listing(
            id=uuid4(),
            managed_account_id=uuid4(),
            bound_group_id=uuid4(),
            group_message_id=12,
            district="east",
            room_count=0,
            price=100,
            summary="bad room count",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        )

    with pytest.raises(ValueError, match="price"):
        Listing(
            id=uuid4(),
            managed_account_id=uuid4(),
            bound_group_id=uuid4(),
            group_message_id=12,
            district="east",
            room_count=1,
            price=0,
            summary="bad price",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        )


def test_viewing_appointment_time_window_is_validated() -> None:
    now = datetime.now(timezone.utc)

    with pytest.raises(ValueError, match="ends_at"):
        ViewingAppointment(
            id=uuid4(),
            managed_account_id=uuid4(),
            conversation_id=uuid4(),
            listing_id=uuid4(),
            telegram_user_id=9001,
            starts_at=now,
            ends_at=now,
            status=AppointmentStatus.PENDING,
            created_at=now,
        )
