CREATE TYPE delivery_status AS ENUM (
'success',
'temporary_failure',
'permanent_failure'
);

CREATE TABLE delivery_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  notification_id UUID NOT NULL,
  attempt_number INT NOT NULL,
  status delivery_status NOT NULL,
  error_message TEXT,
  provider_response JSONB,
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
CREATE INDEX idx_delivery_attempts_notification
ON delivery_attempts(notification_id);