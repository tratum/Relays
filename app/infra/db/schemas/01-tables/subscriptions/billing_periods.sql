CREATE TABLE IF NOT EXISTS billing_periods (
  id UUID PRIMARY KEY NOT NULL DEFAULT gen_random_uuid(),
  subscription_id UUID NOT NULL,
  period_start TIMESTAMPTZ NOT NULL,
  period_end TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
