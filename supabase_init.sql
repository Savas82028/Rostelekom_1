-- Выполните этот скрипт в Supabase SQL Editor (Dashboard → SQL Editor → New query)
-- для создания таблиц приложения Ростелеком.

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Роботы
CREATE TABLE IF NOT EXISTS robots (
    id VARCHAR(50) PRIMARY KEY,
    status VARCHAR(50) DEFAULT 'active',
    battery_level INTEGER,
    last_update TIMESTAMP,
    current_zone VARCHAR(10),
    current_row INTEGER,
    current_shelf INTEGER
);

-- Товары
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    min_stock INTEGER DEFAULT 10,
    optimal_stock INTEGER DEFAULT 100
);

-- История инвентаризации
CREATE TABLE IF NOT EXISTS inventory_history (
    id SERIAL PRIMARY KEY,
    robot_id VARCHAR(50),
    product_id VARCHAR(50),
    quantity INTEGER NOT NULL,
    zone VARCHAR(10) NOT NULL,
    row_number INTEGER,
    shelf_number INTEGER,
    status VARCHAR(50),
    scanned_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Прогнозы ИИ
CREATE TABLE IF NOT EXISTS ai_predictions (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(50),
    prediction_date DATE NOT NULL,
    days_until_stockout INTEGER,
    recommended_order INTEGER,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RLS политики
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE robots ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_predictions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all" ON users;
DROP POLICY IF EXISTS "Allow all" ON robots;
DROP POLICY IF EXISTS "Allow all" ON products;
DROP POLICY IF EXISTS "Allow all" ON inventory_history;
DROP POLICY IF EXISTS "Allow all" ON ai_predictions;

CREATE POLICY "Allow all" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON robots FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON products FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON inventory_history FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON ai_predictions FOR ALL USING (true) WITH CHECK (true);

-- Начальные товары (для эмулятора роботов)
INSERT INTO products (id, name, category) VALUES
    ('TEL-4567', 'Роутер RT-AC68U', 'Сетевое оборудование'),
    ('TEL-8901', 'Модем DSL-2640U', 'Сетевое оборудование'),
    ('TEL-2345', 'Коммутатор SG-108', 'Сетевое оборудование'),
    ('TEL-6789', 'IP-телефон T46S', 'Телефония'),
    ('TEL-3456', 'Кабель UTP Cat6', 'Кабели')
ON CONFLICT (id) DO NOTHING;
