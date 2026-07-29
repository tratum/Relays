CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL,
  created_by UUID NOT NULL,
  name VARCHAR(100) NOT NULL,
  key_prefix VARCHAR(12) NOT NULL,
  key_hash TEXT NOT NULL,
  status api_key_status NOT NULL DEFAULT 'active',
  expires_at TIMESTAMPTZ NULL,
  last_used_at TIMESTAMPTZ NULL,
  revoked_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- CONSTRAINTS
  CONSTRAINT fk_workspace_id
    FOREIGN KEY (workspace_id)
    REFERENCES workspaces(id)
    ON DELETE RESTRICT,

  CONSTRAINT fk_created_by
    FOREIGN KEY (created_by)
    REFERENCES users(id)
    ON DELETE RESTRICT,

  CONSTRAINT chk_name_not_blank
    CHECK (
        length(trim(name)) > 0
    ),

  CONSTRAINT uq_workspace_id_name
    UNIQUE (workspace_id, name),

  CONSTRAINT uq_key_prefix
    UNIQUE (key_prefix),

  CONSTRAINT chk_revoked_State
    CHECK (
      (status = 'active' AND revoked_at IS NULL)
      OR
      (status = 'revoked' AND revoked_at IS NOT NULL)
    )

);

-- INDEXES

CREATE INDEX IF NOT EXISTS idx_api_keys_workspace
ON api_keys(workspace_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_workspace_active
ON api_keys(workspace_id)
WHERE status = 'active';
