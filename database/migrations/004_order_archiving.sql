ALTER TABLE seafood_orders
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

ALTER TABLE seafood_orders
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

UPDATE seafood_orders o
SET completed_at = COALESCE(
    (
        SELECT MAX(h.updated_at)
        FROM order_status_history h
        WHERE h.order_id = o.order_id AND h.status = 'Completed'
    ),
    o.updated_at
)
WHERE o.status = 'Completed' AND o.completed_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_orders_archived_at ON seafood_orders(archived_at);
CREATE INDEX IF NOT EXISTS idx_orders_completed_at ON seafood_orders(completed_at);
