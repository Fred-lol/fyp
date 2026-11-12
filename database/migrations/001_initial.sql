-- AquaLoad initial Supabase PostgreSQL schema.
CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
    phone_number TEXT NOT NULL, address TEXT, city TEXT, state TEXT, postcode TEXT,
    latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL, role TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Active',
    theme_preference TEXT NOT NULL DEFAULT 'System',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS collection_points (
    collection_point_id BIGSERIAL PRIMARY KEY, point_name TEXT NOT NULL UNIQUE, address TEXT,
    city TEXT NOT NULL, state TEXT NOT NULL, postcode TEXT, latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL, status TEXT NOT NULL DEFAULT 'Available',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS seafood_products (
    product_id BIGSERIAL PRIMARY KEY, product_name TEXT NOT NULL UNIQUE, category TEXT NOT NULL,
    description TEXT, unit TEXT NOT NULL DEFAULT 'kg',
    unit_price DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK(unit_price >= 0),
    stock_quantity DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
    availability_status TEXT NOT NULL DEFAULT 'Available', image_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS seafood_orders (
    order_id BIGSERIAL PRIMARY KEY, customer_id BIGINT NOT NULL REFERENCES users(user_id),
    order_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, status TEXT NOT NULL DEFAULT 'Pending',
    collection_point_id BIGINT REFERENCES collection_points(collection_point_id), collection_point TEXT,
    collection_assignment TEXT DEFAULT 'Automatic', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id BIGSERIAL PRIMARY KEY, order_id BIGINT NOT NULL REFERENCES seafood_orders(order_id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES seafood_products(product_id), quantity DOUBLE PRECISION NOT NULL CHECK(quantity > 0), unit TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS order_status_history (
    history_id BIGSERIAL PRIMARY KEY, order_id BIGINT NOT NULL REFERENCES seafood_orders(order_id) ON DELETE CASCADE,
    status TEXT NOT NULL, updated_by BIGINT REFERENCES users(user_id), updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, note TEXT
);
CREATE TABLE IF NOT EXISTS seafood_stock_movements (
    movement_id BIGSERIAL PRIMARY KEY, product_id BIGINT NOT NULL REFERENCES seafood_products(product_id),
    quantity_change DOUBLE PRECISION NOT NULL, movement_type TEXT NOT NULL,
    reference_order_id BIGINT REFERENCES seafood_orders(order_id), updated_by BIGINT REFERENCES users(user_id),
    note TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS payments (
    payment_id BIGSERIAL PRIMARY KEY, order_id BIGINT NOT NULL UNIQUE REFERENCES seafood_orders(order_id) ON DELETE CASCADE,
    customer_id BIGINT NOT NULL REFERENCES users(user_id), amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    payment_method TEXT NOT NULL, payment_status TEXT NOT NULL DEFAULT 'Paid', transaction_reference TEXT NOT NULL UNIQUE,
    paid_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS lorry_profiles (
    lorry_id BIGSERIAL PRIMARY KEY, plate_number TEXT NOT NULL UNIQUE,
    internal_length DOUBLE PRECISION NOT NULL CHECK(internal_length > 0),
    internal_width DOUBLE PRECISION NOT NULL CHECK(internal_width > 0),
    internal_height DOUBLE PRECISION NOT NULL CHECK(internal_height > 0), max_weight DOUBLE PRECISION NOT NULL CHECK(max_weight > 0),
    status TEXT NOT NULL DEFAULT 'Available', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS box_profiles (
    box_profile_id BIGSERIAL PRIMARY KEY, box_name TEXT NOT NULL UNIQUE, capacity_litre INTEGER,
    length DOUBLE PRECISION NOT NULL CHECK(length > 0), width DOUBLE PRECISION NOT NULL CHECK(width > 0), height DOUBLE PRECISION NOT NULL CHECK(height > 0),
    max_seafood_weight_kg DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK(max_seafood_weight_kg >= 0),
    weight_parameter DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK(weight_parameter >= 0), inventory_quantity INTEGER NOT NULL DEFAULT 0 CHECK(inventory_quantity >= 0),
    status TEXT NOT NULL DEFAULT 'Active', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS box_inventory_movements (
    movement_id BIGSERIAL PRIMARY KEY, box_profile_id BIGINT NOT NULL REFERENCES box_profiles(box_profile_id),
    quantity_change INTEGER NOT NULL, movement_type TEXT NOT NULL, updated_by BIGINT REFERENCES users(user_id), note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_box_requirements (
    requirement_id BIGSERIAL PRIMARY KEY, order_id BIGINT NOT NULL REFERENCES seafood_orders(order_id) ON DELETE CASCADE,
    box_profile_id BIGINT NOT NULL REFERENCES box_profiles(box_profile_id), quantity INTEGER NOT NULL CHECK(quantity > 0),
    loaded_weight_per_box DOUBLE PRECISION NOT NULL CHECK(loaded_weight_per_box > 0), created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(order_id, box_profile_id)
);
CREATE TABLE IF NOT EXISTS loading_plans (
    plan_id BIGSERIAL PRIMARY KEY, lorry_id BIGINT NOT NULL REFERENCES lorry_profiles(lorry_id),
    collection_point_id BIGINT REFERENCES collection_points(collection_point_id), created_by BIGINT NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, status TEXT NOT NULL DEFAULT 'Saved', total_boxes INTEGER NOT NULL,
    total_volume DOUBLE PRECISION NOT NULL, used_volume DOUBLE PRECISION NOT NULL, remaining_volume DOUBLE PRECISION NOT NULL,
    space_utilization DOUBLE PRECISION NOT NULL, total_weight DOUBLE PRECISION NOT NULL,
    remaining_weight_capacity DOUBLE PRECISION NOT NULL, validation_result TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS loading_plan_orders (
    plan_id BIGINT NOT NULL REFERENCES loading_plans(plan_id) ON DELETE CASCADE,
    order_id BIGINT NOT NULL REFERENCES seafood_orders(order_id), PRIMARY KEY(plan_id, order_id)
);
CREATE TABLE IF NOT EXISTS box_placements (
    placement_id BIGSERIAL PRIMARY KEY, plan_id BIGINT NOT NULL REFERENCES loading_plans(plan_id) ON DELETE CASCADE,
    order_id BIGINT NOT NULL REFERENCES seafood_orders(order_id), box_profile_id BIGINT NOT NULL REFERENCES box_profiles(box_profile_id),
    box_instance INTEGER NOT NULL, box_label TEXT, x DOUBLE PRECISION NOT NULL, y DOUBLE PRECISION NOT NULL, z DOUBLE PRECISION NOT NULL,
    placed_length DOUBLE PRECISION NOT NULL, placed_width DOUBLE PRECISION NOT NULL, placed_height DOUBLE PRECISION NOT NULL,
    orientation TEXT NOT NULL, sequence_number INTEGER NOT NULL, loaded_weight DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS loading_reports (
    report_id BIGSERIAL PRIMARY KEY, plan_id BIGINT NOT NULL UNIQUE REFERENCES loading_plans(plan_id),
    generated_by BIGINT NOT NULL REFERENCES users(user_id), generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, report_path TEXT
);
CREATE TABLE IF NOT EXISTS lorry_locations (
    location_id BIGSERIAL PRIMARY KEY, lorry_id BIGINT NOT NULL REFERENCES lorry_profiles(lorry_id),
    latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL, accuracy_m DOUBLE PRECISION,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_lower ON users (LOWER(email));
CREATE UNIQUE INDEX IF NOT EXISTS ux_collection_points_name_lower ON collection_points (LOWER(point_name));
CREATE UNIQUE INDEX IF NOT EXISTS ux_products_name_lower ON seafood_products (LOWER(product_name));
CREATE UNIQUE INDEX IF NOT EXISTS ux_lorries_plate_lower ON lorry_profiles (LOWER(plate_number));
CREATE UNIQUE INDEX IF NOT EXISTS ux_boxes_name_lower ON box_profiles (LOWER(box_name));
CREATE INDEX IF NOT EXISTS idx_orders_customer ON seafood_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON seafood_orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_collection ON seafood_orders(collection_point_id);
CREATE INDEX IF NOT EXISTS idx_history_order ON order_status_history(order_id);
CREATE INDEX IF NOT EXISTS idx_placements_plan ON box_placements(plan_id);
CREATE INDEX IF NOT EXISTS idx_stock_product ON seafood_stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_lorry_locations ON lorry_locations(lorry_id, recorded_at DESC);
