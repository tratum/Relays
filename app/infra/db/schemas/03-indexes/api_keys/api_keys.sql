---------------------------
-- API KEYS TABLE
---------------------------

CREATE INDEX IF NOT EXISTS idx_api_keys_workspace
ON api_keys(workspace_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_workspace_active
ON api_keys(workspace_id)
WHERE status = 'active';
