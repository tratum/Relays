ALTER TABLE notifications
  ADD CONSTRAINT chk_channel
    CHECK (
      channel IN ('email','sms','webhook')
    ),

  ADD CONSTRAINT chk_attempt_bounds
    CHECK (
      attempt_count >= 0
      AND max_attempts > 0
      AND attempt_count <= max_attempts
    ),

  ADD CONSTRAINT chk_payload_is_object
    CHECK(jsonb_typeof(payload) = 'object'),

  ADD CONSTRAINT chk_timestamp_sanity
    CHECK (
      (last_attempt_at IS NULL OR last_attempt_at >= created_at)
      AND
      (sent_at IS NULL OR sent_at >= created_at)
    ),

  ADD CONSTRAINT chk_update_after_created
    CHECK(updated_at >= created_at),

  ADD CONSTRAINT recipient_not_empty
    CHECK (length(recipient) > 0),

  ADD CONSTRAINT fk_notifications_workspace
    FOREIGN KEY (workspace_id)
    REFERENCES workspaces(id)
    ON DELETE RESTRICT,

  ADD CONSTRAINT fk_notifications_api_key
    FOREIGN KEY (api_key_id)
    REFERENCES api_keys(id)
    ON DELETE SET NULL,

  ADD CONSTRAINT chk_provider
    CHECK (
      provider IS NULL
      OR provider IN (
        'fake',
        'mailrelay'
      )
    ),

  ADD CONSTRAINT chk_queued_at
    CHECK (
      queued_at IS NULL
      OR queued_at >= created_at
    ),

  ADD CONSTRAINT chk_next_retry_at
    CHECK (
      next_retry_at IS NULL
      OR next_retry_at >= created_at
    ),

  ADD CONSTRAINT chk_sent_at_timestamp
    CHECK (
      (state = 'sent') = (sent_at IS NOT NULL)
    ),

  ADD CONSTRAINT chk_retry_states
    CHECK (
      state IN ('created', 'queued', 'processing')
      OR next_retry_at IS NULL
    );
