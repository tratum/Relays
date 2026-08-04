CREATE INDEX IF NOT EXISTS
idx_user_id
ON workspace_members(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS
uq_workspace_single_owner
ON workspace_members(workspace_id)
WHERE role = 'OWNER';
