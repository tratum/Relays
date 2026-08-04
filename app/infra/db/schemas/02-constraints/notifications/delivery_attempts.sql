ALTER TABLE delivery_attempts
  ADD CONSTRAINT fk_delivery_attempts_notification
    FOREIGN KEY (notification_id)
    REFERENCES notifications(id)
    ON DELETE RESTRICT,

  ADD CONSTRAINT chk_unique_attempt
    UNIQUE (notification_id, attempt_number),

  ADD CONSTRAINT chk_attempt_number
    CHECK (attempt_number >= 1);
