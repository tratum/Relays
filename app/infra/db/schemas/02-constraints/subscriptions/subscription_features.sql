ALTER TABLE features
  ADD CONSTRAINT pk_features
      PRIMARY KEY (id),

  ADD CONSTRAINT uq_feature_key_features
    UNIQUE (feature_key),

  ADD CONSTRAINT chk_feature_key_not_blank_features
    CHECK (length(trim(feature_key)) > 0),

  ADD CONSTRAINT chk_display_name_not_blank_features
    CHECK (length(trim(display_name)) > 0),

  ADD CONSTRAINT chk_description_not_blank_features
    CHECK (length(trim(description)) > 0),

  ADD CONSTRAINT chk_feature_key_lowercase_features
    CHECK (feature_key = lower(feature_key)),

  ADD CONSTRAINT chk_feature_key_format_features
    CHECK (
      feature_key ~ '^[a-z0-9_]+(\.[a-z0-9_]+)+$'
    );
