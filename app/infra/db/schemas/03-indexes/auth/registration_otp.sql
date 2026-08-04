---------------------------
-- REGISTRATION OTP TABLE
---------------------------

CREATE INDEX IF NOT EXISTS idx_registration_otp_active
ON registration_otp(email)
WHERE consumed_at IS NULL;
