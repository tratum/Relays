-- =========================
-- ENUM: notification_state
-- =========================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'notification_state'
    ) THEN
        CREATE TYPE notification_state AS ENUM (
            'created',
            'queued',
            'processing',
            'sent',
            'failed'
        );
    END IF;
END
$$;


-- =========================
-- ENUM: delivery_status
-- =========================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'delivery_status'
    ) THEN
        CREATE TYPE delivery_status AS ENUM (
            'success',
            'temporary_failure',
            'permanent_failure'
        );
    END IF;
END
$$;
