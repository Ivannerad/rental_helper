"""Repositories for listings and listing offers."""

from __future__ import annotations

from uuid import UUID

from shared.domain import LeadRequirements, Listing, ListingOffer, ListingStatus

from ._base import BaseRepository, Session
from ._mappers import (
    LISTING_COLUMNS,
    LISTING_OFFER_COLUMNS,
    listing_from_row,
    listing_offer_from_row,
)


class ListingRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def upsert_listing(self, listing: Listing) -> Listing:
        row = self._fetch_one(
            f"""
            INSERT INTO listings ({LISTING_COLUMNS})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bound_group_id, group_message_id) DO UPDATE
            SET district = EXCLUDED.district,
                room_count = EXCLUDED.room_count,
                price = EXCLUDED.price,
                summary = EXCLUDED.summary,
                status = EXCLUDED.status,
                indexed_at = EXCLUDED.indexed_at
            RETURNING {LISTING_COLUMNS}
            """,
            (
                listing.id,
                listing.managed_account_id,
                listing.bound_group_id,
                listing.group_message_id,
                listing.district,
                listing.room_count,
                listing.price,
                listing.summary,
                listing.status.value,
                listing.indexed_at,
            ),
        )
        assert row is not None
        return listing_from_row(tuple(row))

    def get_listing_by_source(self, bound_group_id: UUID, group_message_id: int) -> Listing | None:
        row = self._fetch_one(
            f"""
            SELECT {LISTING_COLUMNS}
            FROM listings
            WHERE bound_group_id = %s
              AND group_message_id = %s
            """,
            (bound_group_id, group_message_id),
        )
        return None if row is None else listing_from_row(tuple(row))

    def get_listing_by_group_message(
        self, bound_group_id: UUID, group_message_id: int
    ) -> Listing | None:
        return self.get_listing_by_source(bound_group_id, group_message_id)

    def search_listings(
        self,
        managed_account_id: UUID,
        *,
        district: str | None = None,
        room_count: int | None = None,
        max_budget: int | None = None,
    ) -> list[Listing]:
        conditions = [
            "managed_account_id = %s",
            "status = %s",
        ]
        params: list[object] = [managed_account_id, ListingStatus.ACTIVE.value]

        if district is not None:
            conditions.append("district = %s")
            params.append(district)
        if room_count is not None:
            conditions.append("room_count = %s")
            params.append(room_count)
        if max_budget is not None:
            conditions.append("price <= %s")
            params.append(max_budget)

        rows = self._fetch_all(
            f"""
            SELECT {LISTING_COLUMNS}
            FROM listings
            WHERE {" AND ".join(conditions)}
            ORDER BY price ASC, indexed_at DESC
            """,
            params,
        )
        return [listing_from_row(tuple(row)) for row in rows]

    def search_by_requirements(
        self,
        managed_account_id: UUID,
        requirements: LeadRequirements,
    ) -> list[Listing]:
        return self.search_listings(
            managed_account_id,
            district=requirements.district,
            room_count=requirements.room_count,
            max_budget=requirements.max_budget,
        )

    def create_offer(self, offer: ListingOffer) -> ListingOffer | None:
        row = self._fetch_one(
            f"""
            INSERT INTO listing_offers ({LISTING_OFFER_COLUMNS})
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (conversation_id, listing_id) DO NOTHING
            RETURNING {LISTING_OFFER_COLUMNS}
            """,
            (
                offer.id,
                offer.conversation_id,
                offer.listing_id,
                offer.offered_at,
                offer.rejected,
            ),
        )
        return None if row is None else listing_offer_from_row(tuple(row))

    def mark_offer_rejected(self, conversation_id: UUID, listing_id: UUID) -> ListingOffer | None:
        row = self._fetch_one(
            f"""
            UPDATE listing_offers
            SET rejected = TRUE
            WHERE conversation_id = %s
              AND listing_id = %s
            RETURNING {LISTING_OFFER_COLUMNS}
            """,
            (conversation_id, listing_id),
        )
        return None if row is None else listing_offer_from_row(tuple(row))

    def create_listing_offer(self, offer: ListingOffer) -> ListingOffer | None:
        return self.create_offer(offer)

    def reject_offer(self, conversation_id: UUID, listing_id: UUID) -> ListingOffer | None:
        return self.mark_offer_rejected(conversation_id, listing_id)

    def list_offered_listing_ids(self, conversation_id: UUID) -> list[UUID]:
        rows = self._fetch_all(
            """
            SELECT listing_id
            FROM listing_offers
            WHERE conversation_id = %s
            ORDER BY offered_at DESC
            """,
            (conversation_id,),
        )
        return [row[0] for row in rows]
