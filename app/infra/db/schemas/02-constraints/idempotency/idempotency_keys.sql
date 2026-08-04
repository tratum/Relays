ALTER TABLE idempotency_keys
  ADD CONSTRAINT fk_idempotency_api_key
      FOREIGN KEY (api_key_id)
      REFERENCES api_keys(id)
      ON DELETE RESTRICT,

  ADD CONSTRAINT fk_idempotency_notification
    FOREIGN KEY (notification_id)
    REFERENCES notifications(id)
    ON DELETE SET NULL;
