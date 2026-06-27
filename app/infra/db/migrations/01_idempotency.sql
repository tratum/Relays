BEGIN;

-- -----------------
-- Alter Columns
-- -----------------

ALTER TABLE idempotency_keys
ALTER COLUMN request_hash TYPE CHAR(64);

ALTER TABLE idempotency_keys
ALTER COLUMN api_key_id TYPE UUID
USING api_key_id::uuid;

ALTER TABLE idempotency_keys
ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- -----------------
-- Foreign Keys
-- -----------------

ALTER TABLE idempotency_keys
ADD CONSTRAINT fk_idempotency_api_key
FOREIGN KEY (api_key_id)
REFERENCES api_keys(id)
ON DELETE RESTRICT;

ALTER TABLE idempotency_keys
ADD CONSTRAINT fk_idempotency_notification
FOREIGN KEY (notification_id)
REFERENCES notifications(id)
ON DELETE SET NULL;

COMMIT;
