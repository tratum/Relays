---------------------------
-- SESSIONS TABLE
---------------------------

CREATE INDEX IF NOT EXISTS idx_sessions_active_users
ON sessions(user_id)
WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_expiry
ON sessions(expires_at);
