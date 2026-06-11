CREATE TABLE IF NOT EXISTS workspace_members (
  workspace_id UUID NOT NULL,
  user_id UUID NOT NULL,
  role workspace_member_role NOT NULL DEFAULT 'MEMBER',
  joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id,user_id),

  -- CONSTRAINTS
  CONSTRAINT fk_workspace_id
    FOREIGN KEY (workspace_id)
    REFERENCES workspaces(id)
    ON DELETE RESTRICT,

  CONSTRAINT fk_user_id
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE RESTRICT

);

-- INDEXES

CREATE INDEX IF NOT EXISTS
idx_user_id
ON workspace_members(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS
uq_workspace_single_owner
ON workspace_members(workspace_id)
WHERE role = 'OWNER';
