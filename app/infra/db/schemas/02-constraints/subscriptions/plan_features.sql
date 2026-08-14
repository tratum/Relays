ALTER TABLE plan_features
  ADD CONSTRAINT pk_plan_features
    PRIMARY KEY (plan_id, feature_id),

  ADD CONSTRAINT fk_plan_features_plan
    FOREIGN KEY (plan_id)
    REFERENCES plans(id)
    ON DELETE RESTRICT,

  ADD CONSTRAINT fk_plan_features_feature
    FOREIGN KEY (feature_id)
    REFERENCES subscription_features(id)
    ON DELETE RESTRICT;
