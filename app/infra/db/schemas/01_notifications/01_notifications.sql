CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL,
  api_key_id UUID NOT NULL,
  channel TEXT NOT NULL,
  provider TEXT NOT NULL,
  recipient TEXT NOT NULL,
  payload JSONB NOT NULL,
  metadata JSONB,
  state notification_state NOT NULL DEFAULT 'created',
  attempt_count INT NOT NULL DEFAULT 0,
  max_attempts INT NOT NULL DEFAULT 5,
  next_retry_at TIMESTAMPTZ,
  queued_at TIMESTAMPTZ,
  last_attempt_at TIMESTAMPTZ,
  last_error TEXT,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Constraints
  CONSTRAINT chk_channel
    CHECK (
      channel IN ('email','sms','webhook')
    ),

  CONSTRAINT chk_attempt_bounds
    CHECK (
      attempt_count >= 0
      AND max_attempts > 0
      AND attempt_count <= max_attempts
    ),

  CONSTRAINT chk_payload_is_object
    CHECK(jsonb_typeof(payload) = 'object'),

  CONSTRAINT chk_timestamp_sanity
    CHECK (
      (last_attempt_at IS NULL OR last_attempt_at >= created_at)
      AND
      (sent_at IS NULL OR sent_at >= created_at)
    ),

  CONSTRAINT chk_update_after_created
    CHECK(updated_at >= created_at),

  CONSTRAINT recipient_not_empty
    CHECK (length(recipient) > 0),

  CONSTRAINT fk_notifications_workspace
    FOREIGN KEY (workspace_id)
    REFERENCES workspaces(id)
    ON DELETE RESTRICT,

  CONSTRAINT fk_notifications_api_key
    FOREIGN KEY (api_key_id)
    REFERENCES api_keys(id)
    ON DELETE SET NULL,

  CONSTRAINT chk_provider
    CHECK (
      provider IS NULL
      OR provider IN (
        'fake',
        'mailrelay'
      )
    ),

  CONSTRAINT chk_queued_at
  CHECK (
    queued_at IS NULL
    OR queued_at >= created_at
  ),

  CONSTRAINT chk_next_retry_at
  CHECK (
    next_retry_at IS NULL
    OR next_retry_at >= created_at
  ),

  CONSTRAINT chk_sent_at_timestamp
  CHECK (
    (state = 'sent') = (sent_at IS NOT NULL)
  ),

  CONSTRAINT chk_retry_states
    CHECK (
      state IN ('created', 'queued', 'processing')
      OR next_retry_at IS NULL
    )

  );

-- INDEXES
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
