"""Row mapping helpers for persistence repositories."""

from __future__ import annotations

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

MANAGED_ACCOUNT_COLUMNS = "id, telegram_phone, display_name, status, created_at"
BOUND_GROUP_COLUMNS = "id, managed_account_id, telegram_group_id, telegram_group_title, bound_at"
CONVERSATION_COLUMNS = (
    "id, managed_account_id, telegram_user_id, stage, status, district, "
    "room_count, max_budget, handoff_to_human, created_at, updated_at"
)
LISTING_COLUMNS = (
    "id, managed_account_id, bound_group_id, group_message_id, district, "
    "room_count, price, summary, status, indexed_at"
)
LISTING_OFFER_COLUMNS = "id, conversation_id, listing_id, offered_at, rejected"
VIEWING_APPOINTMENT_COLUMNS = (
    "id, managed_account_id, conversation_id, listing_id, telegram_user_id, "
    "starts_at, ends_at, status, created_at"
)


def managed_account_from_row(row: tuple[object, ...]) -> ManagedAccount:
    return ManagedAccount(
        id=row[0],
        telegram_phone=row[1],
        display_name=row[2],
        status=AccountStatus(row[3]),
        created_at=row[4],
    )


def bound_group_from_row(row: tuple[object, ...]) -> BoundGroup:
    return BoundGroup(
        id=row[0],
        managed_account_id=row[1],
        telegram_group_id=row[2],
        telegram_group_title=row[3],
        bound_at=row[4],
    )


def conversation_from_row(row: tuple[object, ...]) -> Conversation:
    return Conversation(
        id=row[0],
        managed_account_id=row[1],
        telegram_user_id=row[2],
        stage=ConversationStage(row[3]),
        status=ConversationStatus(row[4]),
        requirements=LeadRequirements(
            district=row[5],
            room_count=row[6],
            max_budget=row[7],
        ),
        handoff_to_human=row[8],
        created_at=row[9],
        updated_at=row[10],
    )


def listing_from_row(row: tuple[object, ...]) -> Listing:
    return Listing(
        id=row[0],
        managed_account_id=row[1],
        bound_group_id=row[2],
        group_message_id=row[3],
        district=row[4],
        room_count=row[5],
        price=row[6],
        summary=row[7],
        status=ListingStatus(row[8]),
        indexed_at=row[9],
    )


def listing_offer_from_row(row: tuple[object, ...]) -> ListingOffer:
    return ListingOffer(
        id=row[0],
        conversation_id=row[1],
        listing_id=row[2],
        offered_at=row[3],
        rejected=row[4],
    )


def viewing_appointment_from_row(row: tuple[object, ...]) -> ViewingAppointment:
    return ViewingAppointment(
        id=row[0],
        managed_account_id=row[1],
        conversation_id=row[2],
        listing_id=row[3],
        telegram_user_id=row[4],
        starts_at=row[5],
        ends_at=row[6],
        status=AppointmentStatus(row[7]),
        created_at=row[8],
    )


map_managed_account = managed_account_from_row
map_bound_group = bound_group_from_row
map_conversation = conversation_from_row
map_listing = listing_from_row
map_listing_offer = listing_offer_from_row
map_viewing_appointment = viewing_appointment_from_row
