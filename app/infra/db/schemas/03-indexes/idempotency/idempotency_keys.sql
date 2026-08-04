---------------------------
-- IDEMPOTENCY KEYS TABLE
---------------------------

CREATE INDEX IF NOT EXISTS idx_idempotency_lookup
ON idempotency_keys (api_key_id, method, path, idempotency_key);

CREATE INDEX IF NOT EXISTS idx_idempotency_expiry
ON idempotency_keys (expires_at);
