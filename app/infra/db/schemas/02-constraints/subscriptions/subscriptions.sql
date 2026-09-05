ALTER TABLE subscriptions
  ADD CONSTRAINT pk_subscriptions
    PRIMARY KEY (id),

  ADD CONSTRAINT uq_workspace_subscriptions
    UNIQUE (workspace_id),

  ADD CONSTRAINT fk_workspace_subscriptions
    FOREIGN KEY (workspace_id)
    REFERENCES workspaces(id)
    ON DELETE RESTRICT,

  ADD CONSTRAINT fk_plan_subscriptions
    FOREIGN KEY (plan_id)
    REFERENCES plans(id)
    ON DELETE RESTRICT,

  ADD CONSTRAINT chk_status_subscriptions
    CHECK (status IN ('active', 'cancelled')),

  ADD CONSTRAINT chk_cancelled_at_subscriptions
    CHECK (
      (status = 'active' AND cancelled_at IS NULL)
      OR
      (status = 'cancelled' AND cancelled_at IS NOT NULL)
    ),

  ADD CONSTRAINT chk_cancelled_after_started_subscriptions
    CHECK (
      cancelled_at IS NULL
      OR cancelled_at >= started_at
    );


