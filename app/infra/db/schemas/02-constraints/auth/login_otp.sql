ALTER TABLE login_otp
ADD CONSTRAINT pk_id_login_otp
  PRIMARY KEY (id),

ADD CONSTRAINT fk_user_id
  FOREIGN KEY (user_id)
  REFERENCES users(id)
  ON DELETE CASCADE,

ADD CONSTRAINT uq_user_id
  UNIQUE(user_id),

ADD CONSTRAINT chk_consumed_after_creation
  CHECK (
    consumed_at IS NULL
    OR consumed_at >= created_at
  ),

ADD CONSTRAINT chk_expiry_after_creation
  CHECK (expires_at > created_at);
