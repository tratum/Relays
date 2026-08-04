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
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  );
