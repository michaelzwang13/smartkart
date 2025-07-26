-- Select the database
USE hacknyu25;

-- Create the user table (renamed to user_account)
CREATE TABLE user_account (
    user_ID VARCHAR(50),
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    PRIMARY KEY (user_ID)
);

-- Create the shopping_cart table
CREATE TABLE shopping_cart (
    cart_ID INT AUTO_INCREMENT,
    user_ID VARCHAR(50),
    store_name VARCHAR(25) NOT NULL,
    status ENUM('active', 'purchased') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cart_ID),                         
    FOREIGN KEY (user_ID) REFERENCES user_account(user_ID)
);

-- Create the cart_item table
CREATE TABLE cart_item (
    item_ID INT AUTO_INCREMENT,
    cart_ID INT NOT NULL,
    user_ID VARCHAR(50), 
    quantity INT NOT NULL,
    item_name VARCHAR(50) NOT NULL,
    price DECIMAL(10,2),
    upc BIGINT, 
    item_lifetime INT, -- # of DAYS
    image_url VARCHAR(500),
    PRIMARY KEY (item_ID),
    FOREIGN KEY (cart_ID) REFERENCES shopping_cart(cart_ID),
    FOREIGN KEY (user_ID) REFERENCES user_account(user_ID)
);

-- Create the achievements table
CREATE TABLE achievements (
    achievement_ID INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    points INT NOT NULL,
    description VARCHAR(500) NOT NULL,
    PRIMARY KEY (achievement_ID)
);

-- Create the user_achievements table
CREATE TABLE user_achievements (
    user_ID VARCHAR(50),
    achievement_ID INT NOT NULL,
    date_earned DATETIME NOT NULL,
    PRIMARY KEY (user_ID, achievement_ID),
    FOREIGN KEY (user_ID) REFERENCES user_account(user_ID),
    FOREIGN KEY (achievement_ID) REFERENCES achievements(achievement_ID)
);

-- Create the budget table
CREATE TABLE budget (
    budget_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    list_id INT NULL,  -- optional link to a specific shopping list
    allocated_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,  -- planned budget
    total_spent DECIMAL(10, 2) DEFAULT 0.00,               -- running total
    remaining_amount DECIMAL(10, 2) GENERATED ALWAYS AS (allocated_amount - total_spent) STORED,
    alert_threshold DECIMAL(5, 2) DEFAULT 0.80,             -- trigger alert when 80% of budget used
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (budget_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    FOREIGN KEY (list_id) REFERENCES shopping_lists(list_id)
);

-- Create user budget settings table for preferences
CREATE TABLE user_budget_settings (
    user_id VARCHAR(50) PRIMARY KEY,
    monthly_budget DECIMAL(10, 2) DEFAULT 1000.00,
    budget_period ENUM('weekly', 'biweekly', 'monthly') DEFAULT 'monthly',
    alert_threshold DECIMAL(5, 2) DEFAULT 80.00,
    category_limits_enabled BOOLEAN DEFAULT TRUE,
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID)
);

-- Create the shopping_lists table (list metadata)
CREATE TABLE shopping_lists (
    list_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    list_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (list_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID)
);

-- Create the shopping_list_items table (individual items)
CREATE TABLE shopping_list_items (
    item_id INT AUTO_INCREMENT,
    list_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    notes TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id),
    FOREIGN KEY (list_id) REFERENCES shopping_lists(list_id) ON DELETE CASCADE
);

-- GAMIFICATION SYSTEM TABLES

-- Create the user_progress table for XP and levels
CREATE TABLE user_progress (
    user_id VARCHAR(50) PRIMARY KEY,
    total_xp INT NOT NULL DEFAULT 0,
    current_level INT NOT NULL DEFAULT 1,
    meals_cooked_total INT NOT NULL DEFAULT 0,
    items_used_before_expiry INT NOT NULL DEFAULT 0,
    items_expired INT NOT NULL DEFAULT 0,
    total_items_added INT NOT NULL DEFAULT 0,
    days_active INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID)
);

-- Create the user_streaks table for tracking streaks
CREATE TABLE user_streaks (
    user_id VARCHAR(50) PRIMARY KEY,
    cooking_streak_days INT NOT NULL DEFAULT 0,
    cooking_streak_last_date DATE NULL,
    under_budget_streak INT NOT NULL DEFAULT 0,
    under_budget_streak_last_date DATE NULL,
    days_active_streak INT NOT NULL DEFAULT 0,
    days_active_streak_last_date DATE NULL,
    waste_avoidance_streak INT NOT NULL DEFAULT 0,
    waste_avoidance_streak_last_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID)
);

-- Create the meals_logged table for tracking meal history
CREATE TABLE meals_logged (
    meal_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    date_logged DATE NOT NULL,
    recipe_id VARCHAR(100) NULL,
    meal_name VARCHAR(200) NULL,
    xp_earned INT NOT NULL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (meal_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    INDEX idx_user_date (user_id, date_logged)
);

-- Create the pantry_updates table for tracking pantry activity
CREATE TABLE pantry_updates (
    update_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    date_updated DATE NOT NULL,
    items_added INT NOT NULL DEFAULT 0,
    items_removed INT NOT NULL DEFAULT 0,
    xp_earned INT NOT NULL DEFAULT 2,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (update_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    INDEX idx_user_date (user_id, date_updated)
);

-- Create the virtual_items table for unlockable kitchen items
CREATE TABLE virtual_items (
    item_id INT AUTO_INCREMENT,
    item_name VARCHAR(100) NOT NULL,
    item_category ENUM('kitchen_decor', 'pantry_shelves', 'aesthetic_items', 'appliances', 'tools') NOT NULL,
    item_icon VARCHAR(10) NOT NULL, -- emoji or icon identifier
    unlock_type ENUM('level', 'achievement', 'streak') NOT NULL,
    unlock_requirement INT NOT NULL, -- level number, achievement ID, or streak days
    unlock_description VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id)
);

-- Create the user_owned_items table for tracking user's virtual items
CREATE TABLE user_owned_items (
    user_id VARCHAR(50),
    item_id INT,
    date_unlocked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, item_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    FOREIGN KEY (item_id) REFERENCES virtual_items(item_id)
);

-- Create the xp_transactions table for detailed XP tracking
CREATE TABLE xp_transactions (
    transaction_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    xp_amount INT NOT NULL,
    xp_source ENUM('meal_cooked', 'item_used', 'daily_active', 'streak_bonus', 'achievement') NOT NULL,
    source_reference_id INT NULL, -- meal_id, pantry_update_id, etc.
    description VARCHAR(200) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (transaction_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    INDEX idx_user_date (user_id, created_at)
);

-- INSERT INITIAL DATA FOR GAMIFICATION SYSTEM

-- Kitchen Appliances and Tools (Level-based unlocks)
INSERT INTO virtual_items (item_name, item_category, item_icon, unlock_type, unlock_requirement, unlock_description) VALUES
('Basic Stove', 'appliances', '🔥', 'level', 1, 'Every chef needs to start somewhere'),
('Wooden Cutting Board', 'tools', '🪵', 'level', 1, 'Essential for meal prep'),
('Chef\'s Knife', 'tools', '🔪', 'level', 1, 'Your trusty kitchen companion'),
('Basic Pantry Shelf', 'pantry_shelves', '📦', 'level', 1, 'Store your ingredients safely'),
('Spice Rack', 'kitchen_decor', '🧂', 'level', 2, 'Organize your seasonings'),
('Electric Mixer', 'appliances', '🥄', 'level', 6, 'For baking and cooking'),
('Food Processor', 'appliances', '⚙️', 'level', 8, 'Chop, slice, and dice with ease'),
('Stand Mixer', 'appliances', '🥣', 'level', 10, 'Professional-grade mixing power'),
('Espresso Machine', 'appliances', '☕', 'level', 12, 'Start your day right'),
('Wine Fridge', 'appliances', '🍷', 'level', 15, 'For the sophisticated cook');

-- Streak-based unlocks
INSERT INTO virtual_items (item_name, item_category, item_icon, unlock_type, unlock_requirement, unlock_description) VALUES
('Golden Spatula', 'tools', '🥄', 'streak', 7, 'Unlock with 7-day cooking streak'),
('Premium Spice Set', 'kitchen_decor', '🌶️', 'streak', 15, 'Unlock with 15-day cooking streak'),
('Master Chef Hat', 'kitchen_decor', '👨‍🍳', 'streak', 30, 'Unlock with 30-day cooking streak'),
('Budget Tracker Badge', 'aesthetic_items', '💰', 'streak', 30, 'Unlock with 30-day budget streak'),
('Eco-Friendly Containers', 'tools', '♻️', 'streak', 14, 'Unlock with 14-day no-waste streak'),
('Zero Waste Trophy', 'aesthetic_items', '🏆', 'streak', 30, 'Unlock with 30-day no-waste streak');

-- Achievement-based unlocks
INSERT INTO virtual_items (item_name, item_category, item_icon, unlock_type, unlock_requirement, unlock_description) VALUES
('Kitchen Island', 'kitchen_decor', '🏝️', 'achievement', 1, 'Complete first milestone achievement'),
('Herb Garden', 'kitchen_decor', '🌿', 'achievement', 2, 'Complete garden achievement'),
('Fancy Dinnerware', 'aesthetic_items', '🍽️', 'achievement', 3, 'Complete dining achievement'),
('Professional Cookbooks', 'aesthetic_items', '📚', 'achievement', 4, 'Complete knowledge achievement'),
('Kitchen Window View', 'aesthetic_items', '🪟', 'achievement', 5, 'Complete ambiance achievement');
