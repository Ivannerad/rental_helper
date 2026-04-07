# Database Schema

The database schema in this repository is defined by SQL migrations in `src/shared/persistence/migrations/`. It is not modeled with Pydantic.

The current source of truth is `src/shared/persistence/migrations/0001_initial_schema.up.sql`.

## Core tables

- `managed_accounts`
  - columns: `id`, `telegram_phone`, `display_name`, `status`, `created_at`
  - constraints: primary key on `id`, unique `telegram_phone`
- `bound_groups`
  - columns: `id`, `managed_account_id`, `telegram_group_id`, `telegram_group_title`, `bound_at`
  - constraints: foreign key to `managed_accounts`, unique `managed_account_id`, unique `(managed_account_id, telegram_group_id)`
- `conversations`
  - columns: `id`, `managed_account_id`, `telegram_user_id`, `stage`, `status`, `district`, `room_count`, `max_budget`, `handoff_to_human`, `created_at`, `updated_at`
  - constraints: foreign key to `managed_accounts`, unique `(id, managed_account_id)`
  - note: `LeadRequirements` is stored in denormalized columns `district`, `room_count`, `max_budget`
- `listings`
  - columns: `id`, `managed_account_id`, `bound_group_id`, `group_message_id`, `district`, `room_count`, `price`, `summary`, `status`, `indexed_at`
  - constraints: foreign key to `managed_accounts`, composite foreign key to `bound_groups`, unique `(bound_group_id, group_message_id)`, unique `(id, managed_account_id)`
- `listing_offers`
  - columns: `id`, `conversation_id`, `listing_id`, `offered_at`, `rejected`
  - constraints: foreign keys to `conversations` and `listings`, unique `(conversation_id, listing_id)`
- `viewing_appointments`
  - columns: `id`, `managed_account_id`, `conversation_id`, `listing_id`, `telegram_user_id`, `starts_at`, `ends_at`, `status`, `created_at`
  - constraints: foreign key to `managed_accounts`, composite foreign keys to `conversations` and `listings`, check `ends_at > starts_at`

## Relevant indexes

- `ix_conversations_account_user` on `(managed_account_id, telegram_user_id)`
- `ix_conversations_status_stage` on `(status, stage)`
- `ix_listings_lookup` on `(managed_account_id, district, room_count, price, status)`
- `ix_listing_offers_conversation_time` on `(conversation_id, offered_at DESC)`
- `ix_viewing_appointments_account_starts_at` on `(managed_account_id, starts_at)`
- `ix_viewing_appointments_status_starts_at` on `(status, starts_at)`

## Repository-wide storage assumptions

- One bound group exists per managed account.
- Listing identity inside a bound group is anchored by `group_message_id`.
- Offer deduplication is enforced by `(conversation_id, listing_id)`.
- Appointment ownership must remain consistent with both conversation ownership and listing ownership.

## Source of truth rule

- If a task needs database structure, prefer the migration files and this summary over reading unrelated implementation code.
- If a migration changes table shape, indexes, or constraints, update this file in the same change.
