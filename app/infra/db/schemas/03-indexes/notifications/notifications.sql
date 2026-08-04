---------------------------
-- NOTIFICATIONS TABLE
---------------------------

CREATE INDEX IF NOT EXISTS idx_notification_state
ON notifications(state);

CREATE INDEX IF NOT EXISTS idx_notification_channel
ON notifications(channel);

CREATE INDEX IF NOT EXISTS idx_notification_created
ON notifications(created_at);

CREATE INDEX IF NOT EXISTS idx_notification_retry
ON notifications(next_retry_at)
WHERE state IN ('created', 'queued', 'processing');

CREATE INDEX IF NOT EXISTS idx_notifications_workspace
ON notifications(workspace_id);

CREATE INDEX IF NOT EXISTS idx_notifications_api_key
ON notifications(api_key_id);

CREATE INDEX IF NOT EXISTS idx_notifications_workspace_created
ON notifications(
    workspace_id,
    created_at DESC
);
