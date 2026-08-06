CREATE TABLE IF NOT EXISTS plans (
  id SMALLINT NOT NULL,
  slug VARCHAR(100) NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  price_cents INTEGER NOT NULL,
  included_units INTEGER NOT NULL,
  api_key_limit SMALLINT NOT NULL,
  notifications_per_second SMALLINT NOT NULL,
  log_retention_days SMALLINT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
