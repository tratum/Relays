BEGIN;

-- -------------
-- Add Columns
-- -------------

ALTER TABLE notifications
ADD COLUMN workspace_id UUID NOT NULL,
ADD COLUMN api_key_id UUID NOT NULL,
ADD COLUMN provider TEXT NOT NULL;

-- -------------------
-- Delete Constraints
-- -------------------
ALTER TABLE notifications
DROP CONSTRAINT IF EXISTS chk_sent_at_timestamp;

-- -----------------
-- Add Constraints
-- -----------------

ALTER TABLE notifications
ADD CONSTRAINT fk_notifications_workspace
FOREIGN KEY (workspace_id)
REFERENCES workspaces(id)
ON DELETE RESTRICT,

ADD CONSTRAINT fk_notifications_api_key
FOREIGN KEY (api_key_id)
REFERENCES api_keys(id)
ON DELETE SET NULL,

ADD CONSTRAINT chk_provider
CHECK (
  provider IS NULL
  OR provider IN (
    'fake',
    'mailrelay'
  )
),

ADD CONSTRAINT chk_queued_at
CHECK (
  queued_at IS NULL
  OR queued_at >= created_at
),

ADD CONSTRAINT chk_next_retry_at
CHECK (
  next_retry_at IS NULL
  OR next_retry_at >= created_at
),

ADD CONSTRAINT chk_sent_at_timestamp
CHECK (
  (state = 'sent') = (sent_at IS NOT NULL)
),

ADD CONSTRAINT chk_retry_states
CHECK (
  state IN ('created', 'queued', 'processing')
  OR next_retry_at IS NULL
);

-- -------------
-- Add Indexes
-- -------------

CREATE INDEX IF NOT EXISTS idx_notifications_workspace
ON notifications(workspace_id);

CREATE INDEX IF NOT EXISTS idx_notifications_api_key
ON notifications(api_key_id);

CREATE INDEX IF NOT EXISTS idx_notifications_workspace_created
ON notifications(
    workspace_id,
    created_at DESC
);

COMMIT;
