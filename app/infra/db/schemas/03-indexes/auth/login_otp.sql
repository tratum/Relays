---------------------------
-- LOGIN OTP TABLE
---------------------------

CREATE INDEX IF NOT EXISTS idx_login_otp_active
ON login_otp(user_id)
WHERE consumed_at IS NULL;
