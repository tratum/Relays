-- ====================================
-- Enable pgcrypto for UUID Generation
-- ====================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ==========================================
-- Enable GiST Indexes for Range Operations
-- ==========================================
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- =========================
-- ENUM: idempotency_state
-- =========================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'idempotency_state'
    ) THEN
        CREATE TYPE idempotency_state AS ENUM (
            'processing',
            'completed',
            'failed'
        );
    END IF;
END
$$;


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
        CREATE TYPE workspace_member_role AS ENUM (
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
        CREATE TYPE workspace_status AS ENUM (
            'ACTIVE',
            'SUSPENDED',
            'DELETED'
        );
    END IF;
END
$$;

-- =========================
-- ENUM: api_key_status
-- =========================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'api_key_status'
    ) THEN
        CREATE TYPE api_key_status AS ENUM (
            'active',
            'revoked'
        );
    END IF;
END
$$;
