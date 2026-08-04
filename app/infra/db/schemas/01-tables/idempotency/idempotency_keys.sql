CREATE TABLE IF NOT EXISTS idempotency_keys (
  id BIGSERIAL PRIMARY KEY,
  idempotency_key TEXT NOT NULL,
  request_hash CHAR(64) NOT NULL,
  api_key_id UUID NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  notification_id UUID,
  status idempotency_state NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,

  UNIQUE (api_key_id, method, path, idempotency_key)
);
