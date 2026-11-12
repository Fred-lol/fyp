-- Historical plans were packed from the rear-gate coordinate. Keep that fact
-- so the application can render them deep-end first. New plans use 'Deep'.
ALTER TABLE loading_plans
    ADD COLUMN IF NOT EXISTS packing_origin TEXT NOT NULL DEFAULT 'Gate';
