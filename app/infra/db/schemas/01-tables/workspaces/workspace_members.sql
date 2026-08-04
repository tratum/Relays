CREATE TABLE IF NOT EXISTS workspace_members (
  workspace_id UUID NOT NULL,
  user_id UUID NOT NULL,
  role workspace_member_role NOT NULL DEFAULT 'MEMBER',
  joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id,user_id)
);
