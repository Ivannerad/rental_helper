BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS managed_accounts (
    id UUID PRIMARY KEY,
    telegram_phone TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'active', 'stopped')),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS bound_groups (
    id UUID PRIMARY KEY,
    managed_account_id UUID NOT NULL REFERENCES managed_accounts(id) ON DELETE CASCADE,
    telegram_group_id BIGINT NOT NULL,
    telegram_group_title TEXT NOT NULL,
    bound_at TIMESTAMPTZ NOT NULL,
    UNIQUE (managed_account_id),
    UNIQUE (id, managed_account_id),
    UNIQUE (managed_account_id, telegram_group_id)
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    managed_account_id UUID NOT NULL REFERENCES managed_accounts(id) ON DELETE CASCADE,
    telegram_user_id BIGINT NOT NULL,
    stage TEXT NOT NULL CHECK (stage IN ('collecting', 'searching', 'viewing', 'upsell')),
    status TEXT NOT NULL CHECK (status IN ('open', 'paused', 'closed')),
    district TEXT,
    room_count INTEGER CHECK (room_count IS NULL OR room_count > 0),
    max_budget INTEGER CHECK (max_budget IS NULL OR max_budget > 0),
    handoff_to_human BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (id, managed_account_id)
);

CREATE TABLE IF NOT EXISTS listings (
    id UUID PRIMARY KEY,
    managed_account_id UUID NOT NULL REFERENCES managed_accounts(id) ON DELETE CASCADE,
    bound_group_id UUID NOT NULL,
    group_message_id BIGINT NOT NULL,
    district TEXT NOT NULL,
    room_count INTEGER NOT NULL CHECK (room_count > 0),
    price INTEGER NOT NULL CHECK (price > 0),
    summary TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'archived')),
    indexed_at TIMESTAMPTZ NOT NULL,
    UNIQUE (id, managed_account_id),
    FOREIGN KEY (bound_group_id, managed_account_id)
        REFERENCES bound_groups(id, managed_account_id)
        ON DELETE CASCADE,
    UNIQUE (bound_group_id, group_message_id)
);

CREATE TABLE IF NOT EXISTS listing_offers (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    offered_at TIMESTAMPTZ NOT NULL,
    rejected BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (conversation_id, listing_id)
);

CREATE TABLE IF NOT EXISTS viewing_appointments (
    id UUID PRIMARY KEY,
    managed_account_id UUID NOT NULL REFERENCES managed_accounts(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL,
    listing_id UUID NOT NULL,
    telegram_user_id BIGINT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'completed', 'canceled')),
    created_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (conversation_id, managed_account_id)
        REFERENCES conversations(id, managed_account_id)
        ON DELETE CASCADE,
    FOREIGN KEY (listing_id, managed_account_id)
        REFERENCES listings(id, managed_account_id)
        ON DELETE CASCADE,
    CHECK (ends_at > starts_at)
);

CREATE TABLE IF NOT EXISTS queue_events (
    id UUID PRIMARY KEY,
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound', 'dead_letter')),
    queue_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    managed_account_id UUID REFERENCES managed_accounts(id) ON DELETE SET NULL,
    conversation_id UUID,
    telegram_user_id BIGINT,
    correlation_id TEXT,
    idempotency_key TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'received',
    error_message TEXT,
    CHECK (
        conversation_id IS NULL
        OR managed_account_id IS NOT NULL
    ),
    FOREIGN KEY (conversation_id, managed_account_id)
        REFERENCES conversations(id, managed_account_id)
        ON DELETE SET NULL (conversation_id)
);

CREATE TABLE IF NOT EXISTS account_audit_logs (
    id UUID PRIMARY KEY,
    managed_account_id UUID NOT NULL REFERENCES managed_accounts(id) ON DELETE CASCADE,
    actor_telegram_user_id BIGINT,
    action TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_queue_events_idempotency_key
    ON queue_events (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_conversations_account_user
    ON conversations (managed_account_id, telegram_user_id);

CREATE INDEX IF NOT EXISTS ix_conversations_status_stage
    ON conversations (status, stage);

CREATE INDEX IF NOT EXISTS ix_listings_lookup
    ON listings (managed_account_id, district, room_count, price, status);

CREATE INDEX IF NOT EXISTS ix_listing_offers_conversation_time
    ON listing_offers (conversation_id, offered_at DESC);

CREATE INDEX IF NOT EXISTS ix_viewing_appointments_account_starts_at
    ON viewing_appointments (managed_account_id, starts_at);

CREATE INDEX IF NOT EXISTS ix_viewing_appointments_status_starts_at
    ON viewing_appointments (status, starts_at);

CREATE INDEX IF NOT EXISTS ix_queue_events_lookup
    ON queue_events (managed_account_id, conversation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_queue_events_correlation_id
    ON queue_events (correlation_id)
    WHERE correlation_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_queue_events_status_created_at
    ON queue_events (status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_account_audit_logs_account_created_at
    ON account_audit_logs (managed_account_id, created_at DESC);

COMMIT;
