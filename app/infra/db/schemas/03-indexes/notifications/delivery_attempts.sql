---------------------------
-- DELIVERY ATTEMPTS TABLE
---------------------------

CREATE INDEX IF NOT EXISTS idx_delivery_attempt_notification_created
ON delivery_attempts(
    notification_id,
    created_at DESC
);
