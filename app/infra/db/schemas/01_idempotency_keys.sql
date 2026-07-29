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

  UNIQUE (api_key_id, method, path, idempotency_key),

  -- CONSTRAINTS

  CONSTRAINT fk_idempotency_api_key
    FOREIGN KEY (api_key_id)
    REFERENCES api_keys(id)
    ON DELETE RESTRICT,

  CONSTRAINT fk_idempotency_notification
    FOREIGN KEY (notification_id)
    REFERENCES notifications(id)
    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_idempotency_lookup
ON idempotency_keys (api_key_id, method, path, idempotency_key);

CREATE INDEX IF NOT EXISTS idx_idempotency_expiry
ON idempotency_keys (expires_at);
