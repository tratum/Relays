CREATE TABLE idempotency_keys (
  id BIGSERIAL PRIMARY KEY,
  idempotency_key TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  api_key_id BIGINT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  notification_id UUID,
  status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,

  UNIQUE (api_key_id, method, path, idempotency_key)
);

CREATE INDEX idx_idempotency_lookup
ON idempotency_keys (api_key_id, method, path, idempotency_key);

CREATE INDEX idx_idempotency_expiry
ON idempotency_keys (expires_at);
