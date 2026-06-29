BEGIN;

-- -------------
-- Add Columns
-- -------------

ALTER TABLE api_keys
ADD COLUMN created_by UUID NOT NULL;

-- -----------------
-- Add Constraints
-- -----------------

ALTER TABLE api_keys
ADD CONSTRAINT fk_created_by
FOREIGN KEY (created_by)
REFERENCES users(id)
ON DELETE RESTRICT;

COMMIT;
