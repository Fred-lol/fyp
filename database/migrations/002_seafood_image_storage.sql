-- Store seafood product image bytes in Supabase PostgreSQL.
ALTER TABLE seafood_products
    ADD COLUMN IF NOT EXISTS image_data BYTEA,
    ADD COLUMN IF NOT EXISTS image_mime_type TEXT;
