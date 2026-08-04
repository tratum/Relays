ALTER TABLE registration_otp
  ADD CONSTRAINT pk_id_registration_otp
      PRIMARY KEY (id),

  ADD CONSTRAINT uq_email
    UNIQUE(email),

  ADD CONSTRAINT chk_consumed_after_creation
    CHECK (
      consumed_at IS NULL
      OR consumed_at >= created_at
    ),

  ADD CONSTRAINT chk_expiry_after_creation
    CHECK (
      expires_at > created_at
    );
