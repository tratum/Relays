ALTER TABLE sessions
  ADD CONSTRAINT pk_sessions
    PRIMARY KEY (id),

  ADD CONSTRAINT fk_sessions_user_id
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

  ADD CONSTRAINT uq_sessions_refresh_token_hash
    UNIQUE (refresh_token_hash),

  ADD CONSTRAINT chk_session_expiry
    CHECK (expires_at > created_at),

  ADD CONSTRAINT chk_session_revocation
    CHECK (
      revoked_at IS NULL
      OR
      revoked_at >= created_at
    );
