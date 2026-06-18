CREATE TABLE IF NOT EXISTS registration_otp (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL,
  otp_hash TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT pk_id
    PRIMARY KEY (id),

  CONSTRAINT uq_email
    UNIQUE(email),

  CONSTRAINT chk_consumed_after_creation
    CHECK (
      consumed_at IS NULL
      OR consumed_at >= created_at
    ),

  CONSTRAINT chk_expiry_after_creation
    CHECK (
      expires_at > created_at
    )
);

CREATE INDEX IF NOT EXISTS idx_registration_otp_active
ON registration_otp(email)
WHERE consumed_at IS NULL;
