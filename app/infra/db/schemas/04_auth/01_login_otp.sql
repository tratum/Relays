CREATE TABLE IF NOT EXISTS login_otp (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  otp_hash TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT pk_id
    PRIMARY KEY (id),

  CONSTRAINT fk_user_id
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

  CONSTRAINT uq_user_id
    UNIQUE(user_id),

  CONSTRAINT chk_consumed_after_creation
    CHECK (
      consumed_at IS NULL
      OR consumed_at >= created_at
    ),

  CONSTRAINT chk_expiry_after_creation
    CHECK (expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS idx_login_otp_active
ON login_otp(user_id)
WHERE consumed_at IS NULL;
