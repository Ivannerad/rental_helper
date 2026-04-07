# Domain Schema

The domain schema in this repository is implemented as Python dataclasses and enums in `src/shared/domain/models.py`. It is not implemented with Pydantic.

## Entities

- `ManagedAccount`
  - `id: UUID`
  - `telegram_phone: str`
  - `display_name: str`
  - `status: AccountStatus`
  - `created_at: datetime`
- `BoundGroup`
  - `id: UUID`
  - `managed_account_id: UUID`
  - `telegram_group_id: int`
  - `telegram_group_title: str`
  - `bound_at: datetime`
- `LeadRequirements`
  - `district: str | None`
  - `room_count: int | None`
  - `max_budget: int | None`
- `Conversation`
  - `id: UUID`
  - `managed_account_id: UUID`
  - `telegram_user_id: int`
  - `stage: ConversationStage`
  - `status: ConversationStatus`
  - `requirements: LeadRequirements`
  - `handoff_to_human: bool`
  - `created_at: datetime`
  - `updated_at: datetime`
- `Listing`
  - `id: UUID`
  - `managed_account_id: UUID`
  - `bound_group_id: UUID`
  - `group_message_id: int`
  - `district: str`
  - `room_count: int`
  - `price: int`
  - `summary: str`
  - `status: ListingStatus`
  - `indexed_at: datetime`
- `ListingOffer`
  - `id: UUID`
  - `conversation_id: UUID`
  - `listing_id: UUID`
  - `offered_at: datetime`
  - `rejected: bool`
- `ViewingAppointment`
  - `id: UUID`
  - `managed_account_id: UUID`
  - `conversation_id: UUID`
  - `listing_id: UUID`
  - `telegram_user_id: int`
  - `starts_at: datetime`
  - `ends_at: datetime`
  - `status: AppointmentStatus`
  - `created_at: datetime`

## Enum values

- `AccountStatus`: `pending`, `active`, `stopped`
- `ConversationStage`: `collecting`, `searching`, `viewing`, `upsell`
- `ConversationStatus`: `open`, `paused`, `closed`
- `ListingStatus`: `active`, `archived`
- `AppointmentStatus`: `pending`, `confirmed`, `completed`, `canceled`

## Invariants

- `LeadRequirements.room_count` must be positive when present.
- `LeadRequirements.max_budget` must be positive when present.
- `Listing.room_count` must be positive.
- `Listing.price` must be positive.
- `ViewingAppointment.ends_at` must be after `starts_at`.

## Source of truth rule

- If a task needs entity fields or enum values, prefer `src/shared/domain/models.py` over scanning service code.
- If a task changes domain entities, update this file so later tasks can use it as compact context.
