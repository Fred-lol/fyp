-- Completed orders remain safely stored in PostgreSQL for authorised archive
-- review, but are no longer shown in normal operational or customer views.
UPDATE seafood_orders
SET archived_at=COALESCE(archived_at,completed_at,CURRENT_TIMESTAMP)
WHERE status='Completed';
