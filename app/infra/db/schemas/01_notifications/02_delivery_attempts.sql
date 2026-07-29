CREATE TABLE IF NOT EXISTS delivery_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  notification_id UUID NOT NULL,
  attempt_number INT NOT NULL,
  status delivery_status NOT NULL,
  error_message TEXT,
  provider TEXT NOT NULL,
  provider_message_id TEXT,
  provider_error_code TEXT,
  raw_provider_response JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- CONSTRAINTS
  CONSTRAINT fk_delivery_attempts_notification
    FOREIGN KEY (notification_id)
    REFERENCES notifications(id)
    ON DELETE RESTRICT,

  CONSTRAINT chk_unique_attempt
    UNIQUE (notification_id, attempt_number),

  CONSTRAINT chk_attempt_number
    CHECK (attempt_number >= 1)

  );

-- INDEXES

CREATE INDEX IF NOT EXISTS idx_delivery_attempt_notification_created
ON delivery_attempts(
    notification_id,
    created_at DESC
);
