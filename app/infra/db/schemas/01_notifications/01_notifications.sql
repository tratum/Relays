CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel TEXT NOT NULL,
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

  CONSTRAINT chk_sent_at_timestamp
    CHECK (
      (state = 'sent' AND sent_at IS NOT NULL)
      OR
      (state <> 'sent')
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
    CHECK (length(recipient) > 0)

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
