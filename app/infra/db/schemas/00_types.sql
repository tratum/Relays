-- ====================================
-- Enable pgcrypto for UUID Generation
-- ====================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

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

-- =========================
-- ENUM: workspace_member_role
-- =========================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'workspace_member_role'
    ) THEN
        CREATE TYPE delivery_status AS ENUM (
            'OWNER',
            'MEMBER'
        );
    END IF;
END
$$;

-- =========================
-- ENUM: workspace_status
-- =========================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'workspace_status'
    ) THEN
        CREATE TYPE delivery_status AS ENUM (
            'ACTIVE',
            'SUSPENDED',
            'DELETED'
        );
    END IF;
END
$$;
