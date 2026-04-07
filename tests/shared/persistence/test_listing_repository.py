"""Tests for listing and listing-offer repositories."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from shared.domain import (
    AccountStatus,
    BoundGroup,
    Conversation,
    ConversationStage,
    ConversationStatus,
    LeadRequirements,
    Listing,
    ListingOffer,
    ListingStatus,
    ManagedAccount,
)
from shared.persistence import AccountRepository
from shared.persistence.repositories import ConversationRepository, ListingRepository


def test_listing_repository_upserts_and_fetches_by_source(connection) -> None:
    account_repository = AccountRepository(connection)
    listing_repository = ListingRepository(connection)
    now = datetime.now(timezone.utc)
    account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550170",
            display_name="Listing Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    group = account_repository.upsert_bound_group(
        BoundGroup(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_group_id=-100300000001,
            telegram_group_title="Listings Feed",
            bound_at=now,
        )
    )
    first = Listing(
        id=uuid4(),
        managed_account_id=account.id,
        bound_group_id=group.id,
        group_message_id=101,
        district="west",
        room_count=2,
        price=120000,
        summary="Initial summary",
        status=ListingStatus.ACTIVE,
        indexed_at=now,
    )
    replacement = Listing(
        id=uuid4(),
        managed_account_id=account.id,
        bound_group_id=group.id,
        group_message_id=101,
        district="west",
        room_count=3,
        price=125000,
        summary="Updated summary",
        status=ListingStatus.ARCHIVED,
        indexed_at=now + timedelta(minutes=5),
    )

    inserted = listing_repository.upsert_listing(first)
    updated = listing_repository.upsert_listing(replacement)

    assert inserted == first
    assert updated.id == first.id
    assert updated.room_count == replacement.room_count
    assert updated.price == replacement.price
    assert updated.summary == replacement.summary
    assert updated.status is ListingStatus.ARCHIVED
    assert (
        listing_repository.get_listing_by_group_message(group.id, first.group_message_id) == updated
    )


def test_listing_repository_search_filters_active_budget_and_room_count(connection) -> None:
    account_repository = AccountRepository(connection)
    listing_repository = ListingRepository(connection)
    now = datetime.now(timezone.utc)
    account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550171",
            display_name="Search Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    other_account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550172",
            display_name="Other Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    group = account_repository.upsert_bound_group(
        BoundGroup(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_group_id=-100300000002,
            telegram_group_title="Search Feed",
            bound_at=now,
        )
    )
    other_group = account_repository.upsert_bound_group(
        BoundGroup(
            id=uuid4(),
            managed_account_id=other_account.id,
            telegram_group_id=-100300000003,
            telegram_group_title="Other Feed",
            bound_at=now,
        )
    )

    listings = [
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=201,
            district="west",
            room_count=2,
            price=110000,
            summary="match one",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        ),
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=202,
            district="west",
            room_count=2,
            price=140000,
            summary="over budget",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        ),
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=203,
            district="west",
            room_count=1,
            price=90000,
            summary="wrong room count",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        ),
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=204,
            district="west",
            room_count=2,
            price=100000,
            summary="archived",
            status=ListingStatus.ARCHIVED,
            indexed_at=now,
        ),
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=205,
            district="east",
            room_count=2,
            price=105000,
            summary="wrong district",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        ),
        Listing(
            id=uuid4(),
            managed_account_id=other_account.id,
            bound_group_id=other_group.id,
            group_message_id=206,
            district="west",
            room_count=2,
            price=95000,
            summary="other account",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        ),
    ]

    for listing in listings:
        listing_repository.upsert_listing(listing)

    results = listing_repository.search_listings(
        account.id,
        district="west",
        room_count=2,
        max_budget=130000,
    )

    assert [listing.id for listing in results] == [listings[0].id]


def test_listing_repository_protects_duplicate_offers_and_tracks_rejections(connection) -> None:
    account_repository = AccountRepository(connection)
    conversation_repository = ConversationRepository(connection)
    listing_repository = ListingRepository(connection)
    now = datetime.now(timezone.utc)
    account = account_repository.create_account(
        ManagedAccount(
            id=uuid4(),
            telegram_phone="+12025550173",
            display_name="Offer Account",
            status=AccountStatus.ACTIVE,
            created_at=now,
        )
    )
    group = account_repository.upsert_bound_group(
        BoundGroup(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_group_id=-100300000004,
            telegram_group_title="Offer Feed",
            bound_at=now,
        )
    )
    conversation = conversation_repository.create_conversation(
        Conversation(
            id=uuid4(),
            managed_account_id=account.id,
            telegram_user_id=5010,
            stage=ConversationStage.SEARCHING,
            status=ConversationStatus.OPEN,
            requirements=LeadRequirements(district="west", room_count=2, max_budget=130000),
            handoff_to_human=False,
            created_at=now,
            updated_at=now,
        )
    )
    first_listing = listing_repository.upsert_listing(
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=301,
            district="west",
            room_count=2,
            price=115000,
            summary="first offer",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        )
    )
    second_listing = listing_repository.upsert_listing(
        Listing(
            id=uuid4(),
            managed_account_id=account.id,
            bound_group_id=group.id,
            group_message_id=302,
            district="west",
            room_count=2,
            price=118000,
            summary="second offer",
            status=ListingStatus.ACTIVE,
            indexed_at=now,
        )
    )
    first_offer = ListingOffer(
        id=uuid4(),
        conversation_id=conversation.id,
        listing_id=first_listing.id,
        offered_at=now,
    )
    second_offer = ListingOffer(
        id=uuid4(),
        conversation_id=conversation.id,
        listing_id=second_listing.id,
        offered_at=now + timedelta(minutes=1),
    )

    created_first = listing_repository.create_listing_offer(first_offer)
    duplicate = listing_repository.create_listing_offer(first_offer)
    created_second = listing_repository.create_listing_offer(second_offer)
    rejected = listing_repository.mark_offer_rejected(conversation.id, first_listing.id)

    assert created_first == first_offer
    assert duplicate is None
    assert created_second == second_offer
    assert rejected is not None
    assert rejected.rejected is True
    assert listing_repository.list_offered_listing_ids(conversation.id) == [
        second_listing.id,
        first_listing.id,
    ]
