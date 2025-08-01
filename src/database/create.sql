-- Select the database
USE hacknyu25;

-- Create the user table (renamed to user_account)
CREATE TABLE user_account (
    user_ID VARCHAR(50),
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    PRIMARY KEY (user_ID)
);

-- Create the shopping_cart table
CREATE TABLE shopping_cart (
    cart_ID INT AUTO_INCREMENT,
    user_ID VARCHAR(50),
    store_name VARCHAR(25) NOT NULL,
    status ENUM('active', 'purchased') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shopping_list_id INT NULL,
    PRIMARY KEY (cart_ID),                         
    FOREIGN KEY (user_ID) REFERENCES user_account(user_ID),
    FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(list_id)
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

CREATE TABLE shopping_list_cart_mapping (
    mapping_id INT AUTO_INCREMENT,
    cart_id INT NOT NULL,
    list_item_id INT NOT NULL,
    cart_item_id INT NULL, -- NULL if not yet added to cart
    is_found BOOLEAN DEFAULT FALSE, -- Whether the item was found and added during shopping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (mapping_id),
    FOREIGN KEY (cart_id) REFERENCES shopping_cart(cart_ID) ON DELETE CASCADE,
    FOREIGN KEY (list_item_id) REFERENCES shopping_list_items(item_id) ON DELETE CASCADE,
    FOREIGN KEY (cart_item_id) REFERENCES cart_item(item_ID) ON DELETE SET NULL,
    UNIQUE KEY unique_cart_list_item (cart_id, list_item_id)
);

-- Create meal_plans table for storing generated meal plans
CREATE TABLE meal_plans (
    plan_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days INT NOT NULL,
    dietary_preference VARCHAR(50) DEFAULT 'none', -- vegetarian, vegan, keto, paleo, etc.
    budget_limit DECIMAL(10,2) NULL,
    max_cooking_time INT NULL, -- minutes per day
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'completed', 'archived') DEFAULT 'active',
    ai_model_used VARCHAR(50) DEFAULT 'gemini-1.5-flash-latest',
    generation_prompt TEXT NULL, -- store the prompt used for generation
    PRIMARY KEY (plan_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    INDEX idx_user_plans (user_id),
    INDEX idx_plan_dates (start_date, end_date),
    INDEX idx_plan_status (status)
);



-- Create batch_prep_steps table for organizing cooking sessions
CREATE TABLE batch_prep_steps (
    step_id INT AUTO_INCREMENT,
    plan_id INT NOT NULL,
    prep_session_name VARCHAR(100) NOT NULL, -- "Sunday Prep Session", "Wednesday Quick Prep"
    step_order INT NOT NULL,
    description TEXT NOT NULL,
    estimated_time INT NOT NULL, -- minutes
    recipes_involved TEXT NULL, -- JSON array of recipe_ids or comma-separated
    equipment_needed VARCHAR(500) NULL,
    tips TEXT NULL,
    PRIMARY KEY (step_id),
    FOREIGN KEY (plan_id) REFERENCES meal_plans(plan_id) ON DELETE CASCADE,
    INDEX idx_plan_steps (plan_id),
    INDEX idx_step_order (prep_session_name, step_order)
);

-- Create meal_plan_shopping_list table to auto-generate shopping lists from meal plans
CREATE TABLE meal_plan_shopping_list (
    shopping_item_id INT AUTO_INCREMENT,
    plan_id INT NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    total_quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    estimated_cost DECIMAL(8,2) NULL,
    category VARCHAR(50) DEFAULT 'Other',
    is_pantry_available BOOLEAN DEFAULT FALSE, -- if user already has this
    recipes_using TEXT NULL, -- which recipes need this ingredient
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shopping_item_id),
    FOREIGN KEY (plan_id) REFERENCES meal_plans(plan_id) ON DELETE CASCADE,
    INDEX idx_plan_shopping (plan_id),
    INDEX idx_ingredient_category (category)
);

-- Create user_meal_preferences table for storing user preferences
CREATE TABLE user_meal_preferences (
    user_id VARCHAR(50) PRIMARY KEY,
    dietary_restrictions TEXT NULL, -- JSON array of restrictions
    favorite_cuisines TEXT NULL, -- JSON array of cuisines
    disliked_ingredients TEXT NULL, -- JSON array of ingredients to avoid
    cooking_skill_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
    preferred_meal_prep_day ENUM('sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday') DEFAULT 'sunday',
    max_daily_cooking_time INT DEFAULT 60, -- minutes
    preferred_budget_per_meal DECIMAL(6,2) DEFAULT 8.00,
    kitchen_equipment TEXT NULL, -- JSON array of available equipment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID)
);

-- Create recipes table for storing individual recipes
CREATE TABLE recipes (
    recipe_id INT AUTO_INCREMENT,
    plan_id INT NOT NULL,
    meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack') NOT NULL,
    day_number INT NOT NULL, -- which day of the plan (1-7)
    recipe_name VARCHAR(200) NOT NULL,
    description TEXT NULL,
    prep_time INT NULL, -- minutes
    cook_time INT NULL, -- minutes
    servings INT DEFAULT 1,
    estimated_cost DECIMAL(8,2) NULL,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    calories_per_serving INT NULL,
    instructions TEXT NOT NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recipe_id),
    FOREIGN KEY (plan_id) REFERENCES meal_plans(plan_id) ON DELETE CASCADE,
    INDEX idx_plan_recipes (plan_id),
    INDEX idx_day_meal (day_number, meal_type)
);

-- Create recipe_ingredients table for storing ingredients per recipe
CREATE TABLE recipe_ingredients (
    ingredient_id INT AUTO_INCREMENT,
    recipe_id INT NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL, -- cups, tsp, lbs, oz, etc.
    notes VARCHAR(200) NULL, -- "diced", "optional", etc.
    is_pantry_item BOOLEAN DEFAULT FALSE, -- if available in user's pantry
    estimated_cost DECIMAL(6,2) NULL,
    PRIMARY KEY (ingredient_id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    INDEX idx_recipe_ingredients (recipe_id),
    INDEX idx_ingredient_name (ingredient_name)
);

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
('Other', 'pantry', 30),
('Fresh Herbs', 'fridge', 7),
('Oils & Vinegars', 'pantry', 365),
('Baking Supplies', 'pantry', 730);

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
