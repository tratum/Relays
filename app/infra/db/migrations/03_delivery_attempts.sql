BEGIN;

-- -------------
-- Add Columns
-- -------------

ALTER TABLE delivery_attempts
ADD COLUMN provider_message_id TEXT,
ADD COLUMN provider_error_code TEXT,
ADD COLUMN provider TEXT NOT NULL;

-- -------------
-- Add Indexes
-- -------------

CREATE INDEX IF NOT EXISTS idx_delivery_attempt_notification_created
ON delivery_attempts(
    notification_id,
    created_at DESC
);

COMMIT;
