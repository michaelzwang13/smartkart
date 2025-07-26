-- Pantry Integration Database Schema
-- Add these tables to the existing database

USE hacknyu25;

-- Create pantry_items table for tracking user pantry inventory
CREATE TABLE pantry_items (
    pantry_item_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    unit VARCHAR(20) NOT NULL DEFAULT 'pcs', -- pcs, g, ml, kg, lbs, oz, etc.
    category VARCHAR(50) DEFAULT 'Other', -- Produce, Meat, Grains, Dairy, etc.
    storage_type ENUM('pantry', 'fridge', 'freezer') DEFAULT 'pantry',
    expiration_date DATE NULL, -- can be NULL if no expiry
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    source_type ENUM('manual', 'shopping_trip') DEFAULT 'manual',
    source_cart_id INT NULL, -- reference to shopping_cart if from trip
    is_ai_predicted_expiry BOOLEAN DEFAULT FALSE, -- if expiry was AI predicted
    notes TEXT NULL,
    is_consumed BOOLEAN DEFAULT FALSE, -- if item has been used up
    PRIMARY KEY (pantry_item_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    FOREIGN KEY (source_cart_id) REFERENCES shopping_cart(cart_ID),
    INDEX idx_user_pantry (user_id),
    INDEX idx_expiration (expiration_date),
    INDEX idx_category (category)
);

-- Create pantry_categories table for standardized categories
CREATE TABLE pantry_categories (
    category_id INT AUTO_INCREMENT,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    default_storage_type ENUM('pantry', 'fridge', 'freezer') DEFAULT 'pantry',
    typical_shelf_life_days INT NULL, -- default shelf life for category
    PRIMARY KEY (category_id)
);

-- Insert common pantry categories
INSERT INTO pantry_categories (category_name, default_storage_type, typical_shelf_life_days) VALUES
('Produce', 'fridge', 7),
('Meat', 'fridge', 3),
('Dairy', 'fridge', 14),
('Grains', 'pantry', 365),
('Canned Goods', 'pantry', 730),
('Frozen Foods', 'freezer', 90),
('Beverages', 'fridge', 30),
('Snacks', 'pantry', 60),
('Condiments', 'pantry', 180),
('Spices', 'pantry', 1095),
('Bread', 'pantry', 5),
('Other', 'pantry', 30);

-- Create pantry_transfer_sessions table to track bulk transfers from shopping trips
CREATE TABLE pantry_transfer_sessions (
    transfer_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    cart_id INT NOT NULL,
    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    items_transferred INT DEFAULT 0,
    notes TEXT NULL,
    PRIMARY KEY (transfer_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    FOREIGN KEY (cart_id) REFERENCES shopping_cart(cart_ID),
    INDEX idx_user_transfers (user_id),
    INDEX idx_cart_transfers (cart_id)
);

-- Create expiry_predictions table to cache AI predictions and improve performance
CREATE TABLE expiry_predictions (
    prediction_id INT AUTO_INCREMENT,
    item_name VARCHAR(100) NOT NULL,
    storage_type ENUM('pantry', 'fridge', 'freezer') NOT NULL,
    predicted_days INT NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.5, -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_count INT DEFAULT 1, -- how many times this prediction was used
    PRIMARY KEY (prediction_id),
    UNIQUE KEY unique_prediction (item_name, storage_type),
    INDEX idx_item_storage (item_name, storage_type)
);