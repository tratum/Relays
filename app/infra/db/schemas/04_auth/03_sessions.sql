CREATE TABLE IF NOT EXISTS sessions (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  refresh_token_hash TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT pk_sessions
    PRIMARY KEY (id),

  CONSTRAINT fk_sessions_user_id
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

  CONSTRAINT uq_sessions_refresh_token_hash
    UNIQUE (refresh_token_hash),

  CONSTRAINT chk_session_expiry
    CHECK (expires_at > created_at),

  CONSTRAINT chk_session_revocation
    CHECK (
      revoked_at IS NULL
      OR
      revoked_at >= created_at
    )
);

CREATE INDEX IF NOT EXISTS idx_sessions_active_users
ON sessions(user_id)
WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_expiry
ON sessions(expires_at);
