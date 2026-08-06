ALTER TABLE plans
  ADD CONSTRAINT pk_plans
    PRIMARY KEY(id),

  ADD CONSTRAINT uq_slug_plans
    UNIQUE (slug),

  ADD CONSTRAINT chk_slug_lowercase_plans
    CHECK (
        slug = lower(slug)
        AND length(trim(slug)) > 0
    ),

  ADD CONSTRAINT chk_price_cents_plans
    CHECK (price_cents >= 0),

  ADD CONSTRAINT chk_included_units_plans
    CHECK (included_units >= 0),

  ADD CONSTRAINT chk_api_key_limit_plans
    CHECK (api_key_limit > 0),

  ADD CONSTRAINT chk_notifications_per_second_plans
    CHECK (notifications_per_second > 0),

  ADD CONSTRAINT chk_log_retention_days_plans
    CHECK (log_retention_days > 0);
