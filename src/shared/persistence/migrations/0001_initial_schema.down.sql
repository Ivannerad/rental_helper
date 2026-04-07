BEGIN;

DROP TABLE IF EXISTS account_audit_logs;
DROP TABLE IF EXISTS queue_events;
DROP TABLE IF EXISTS viewing_appointments;
DROP TABLE IF EXISTS listing_offers;
DROP TABLE IF EXISTS listings;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS bound_groups;
DROP TABLE IF EXISTS managed_accounts;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = current_schema()
          AND table_name = 'schema_migrations'
    ) THEN
        DELETE FROM schema_migrations
        WHERE version = '0001_initial_schema';
    END IF;
END $$;

COMMIT;
