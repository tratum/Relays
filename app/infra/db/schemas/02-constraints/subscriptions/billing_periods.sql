ALTER TABLE billing_periods
  ADD CONSTRAINT pk_billing_periods
    PRIMARY KEY(id),

  ADD CONSTRAINT uq_period_start_billing_periods
    UNIQUE(subscription_id, period_start),

  ADD CONSTRAINT fk_subscription_id_billing_periods
    FOREIGN KEY (subscription_id)
    REFERENCES subscriptions(id)
    ON DELETE RESTRICT,

  ADD CONSTRAINT chk_period_end_after_period_start
    CHECK (period_end > period_start),

  ADD CONSTRAINT ex_no_overlap_billing_periods
    EXCLUDE USING GIST (
      subscription_id WITH =,
      tstzrange(period_start, period_end, '[)') WITH &&
    );
