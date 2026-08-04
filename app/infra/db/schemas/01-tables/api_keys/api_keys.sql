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
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
