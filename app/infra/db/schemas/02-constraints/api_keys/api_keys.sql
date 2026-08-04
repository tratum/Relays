ALTER TABLE api_keys
  ADD CONSTRAINT fk_workspace_id
    FOREIGN KEY (workspace_id)
    REFERENCES workspaces(id)
    ON DELETE RESTRICT,

  ADD CONSTRAINT fk_created_by
    FOREIGN KEY (created_by)
    REFERENCES users(id)
    ON DELETE RESTRICT,

  ADD CONSTRAINT chk_name_not_blank
    CHECK (
        length(trim(name)) > 0
    ),

  ADD CONSTRAINT uq_workspace_id_name
    UNIQUE (workspace_id, name),

  ADD CONSTRAINT uq_key_prefix
    UNIQUE (key_prefix),

  ADD CONSTRAINT chk_revoked_State
    CHECK (
      (status = 'active' AND revoked_at IS NULL)
      OR
      (status = 'revoked' AND revoked_at IS NOT NULL)
    );
