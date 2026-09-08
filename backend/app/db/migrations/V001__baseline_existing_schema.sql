-- Baseline migration for databases initialized before recipe-order-system.
-- This file is versioned and must never be edited after it is applied.

DO $$
BEGIN
    IF to_regclass('public.users') IS NULL THEN
        RAISE EXCEPTION 'required table public.users does not exist';
    END IF;
END $$;

-- Preserve existing users when the database volume predates the role system.
ALTER TABLE users
ADD COLUMN IF NOT EXISTS role VARCHAR(20);

UPDATE users
SET role = 'user'
WHERE role IS NULL;

ALTER TABLE users
ALTER COLUMN role SET DEFAULT 'user';

ALTER TABLE users
ALTER COLUMN role SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'users_role_check'
          AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users
        ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'user'));
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS recipe_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL DEFAULT 0,
    image_url VARCHAR(500),
    category_id INTEGER NOT NULL REFERENCES recipe_categories(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT recipes_status_check CHECK (status IN ('active', 'inactive'))
);

CREATE INDEX IF NOT EXISTS recipes_category_status_idx
ON recipes (category_id, status);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT orders_status_check
        CHECK (status IN ('pending', 'completed', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0)
);

CREATE INDEX IF NOT EXISTS orders_user_id_created_at_idx
ON orders (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS order_items_order_id_idx
ON order_items (order_id);
