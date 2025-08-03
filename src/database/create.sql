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

-- Create tags table to store unique tags per user
CREATE TABLE pantry_tags (
    tag_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    tag_name VARCHAR(50) NOT NULL,
    tag_color VARCHAR(7) DEFAULT '#3B82F6', -- hex color code for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INT DEFAULT 0, -- track how often tag is used
    PRIMARY KEY (tag_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID) ON DELETE CASCADE,
    UNIQUE KEY unique_user_tag (user_id, tag_name), -- prevent duplicate tags per user
    INDEX idx_user_tags (user_id),
    INDEX idx_tag_name (tag_name)
);

-- Create junction table for many-to-many relationship between pantry items and tags
CREATE TABLE pantry_item_tags (
    item_tag_id INT AUTO_INCREMENT,
    pantry_item_id INT NOT NULL,
    tag_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_tag_id),
    FOREIGN KEY (pantry_item_id) REFERENCES pantry_items(pantry_item_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES pantry_tags(tag_id) ON DELETE CASCADE,
    UNIQUE KEY unique_item_tag (pantry_item_id, tag_id), -- prevent duplicate tag assignments
    INDEX idx_item_tags (pantry_item_id),
    INDEX idx_tag_items (tag_id)
);

-- Create monthly meal goals table
CREATE TABLE monthly_meal_goals (
    goal_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    month INT NOT NULL CHECK (month >= 1 AND month <= 12),
    year INT NOT NULL CHECK (year >= 2020 AND year <= 2030),
    meal_plans_goal INT DEFAULT 4 CHECK (meal_plans_goal >= 1 AND meal_plans_goal <= 20),
    meals_completed_goal INT DEFAULT 60 CHECK (meals_completed_goal >= 10 AND meals_completed_goal <= 200),
    new_recipes_goal INT DEFAULT 12 CHECK (new_recipes_goal >= 1 AND new_recipes_goal <= 50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (goal_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID) ON DELETE CASCADE,
    UNIQUE KEY unique_user_month (user_id, month, year),
    INDEX idx_user_goals (user_id),
    INDEX idx_month_year (month, year)
);

-- Create recipe_templates table for storing reusable recipe templates
CREATE TABLE recipe_templates (
    template_id INT AUTO_INCREMENT,
    recipe_name VARCHAR(200) NOT NULL,
    description TEXT NULL,
    meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack') NOT NULL,
    prep_time INT NULL, -- minutes
    cook_time INT NULL, -- minutes
    servings INT DEFAULT 1,
    estimated_cost DECIMAL(8,2) NULL,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    calories_per_serving INT NULL,
    instructions TEXT NOT NULL,
    cuisine_type VARCHAR(50) NULL, -- Italian, Mexican, Asian, etc.
    dietary_tags TEXT NULL, -- JSON array of dietary tags (vegetarian, gluten-free, etc.)
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (template_id),
    INDEX idx_recipe_name (recipe_name),
    INDEX idx_meal_type (meal_type),
    INDEX idx_cuisine_type (cuisine_type),
    INDEX idx_difficulty (difficulty)
);

-- Create template_ingredients table for storing ingredients per recipe template
CREATE TABLE template_ingredients (
    ingredient_id INT AUTO_INCREMENT,
    template_id INT NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL, -- cups, tsp, lbs, oz, etc.
    notes VARCHAR(200) NULL, -- "diced", "optional", etc.
    is_pantry_item BOOLEAN DEFAULT FALSE, -- if typically available in user's pantry
    estimated_cost DECIMAL(6,2) NULL,
    PRIMARY KEY (ingredient_id),
    FOREIGN KEY (template_id) REFERENCES recipe_templates(template_id) ON DELETE CASCADE,
    INDEX idx_template_ingredients (template_id),
    INDEX idx_ingredient_name (ingredient_name)
);

-- Create meal_plan_sessions table for storing meal planning sessions
CREATE TABLE meal_plan_sessions (
    session_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    session_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days INT NOT NULL,
    dietary_preference VARCHAR(50) DEFAULT 'none', -- vegetarian, vegan, keto, paleo, etc.
    max_cooking_time INT NULL, -- minutes per day
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'completed', 'archived') DEFAULT 'active',
    ai_model_used VARCHAR(50) DEFAULT 'gemini-1.5-flash-latest',
    generation_prompt TEXT NULL, -- store the prompt used for generation
    PRIMARY KEY (session_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    INDEX idx_user_sessions (user_id),
    INDEX idx_session_dates (start_date, end_date),
    INDEX idx_session_status (status)
);

-- Create meals table for storing individual meal instances
CREATE TABLE meals (
    meal_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    meal_date DATE NOT NULL,
    meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack') NOT NULL,
    recipe_template_id INT NULL, -- reference to recipe template (if using template)
    session_id INT NULL, -- reference to meal plan session (if part of plan)
    custom_recipe_name VARCHAR(200) NULL, -- if not using template
    custom_instructions TEXT NULL, -- if not using template
    is_completed BOOLEAN DEFAULT FALSE,
    completion_date TIMESTAMP NULL,
    notes TEXT NULL,
    is_locked BOOLEAN DEFAULT FALSE, -- prevents AI from overwriting
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (meal_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID),
    FOREIGN KEY (recipe_template_id) REFERENCES recipe_templates(template_id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES meal_plan_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_user_meals (user_id),
    INDEX idx_meal_date (meal_date),
    INDEX idx_meal_type (meal_type),
    INDEX idx_session_meals (session_id),
    INDEX idx_template_meals (recipe_template_id),
    UNIQUE KEY unique_user_meal_slot (user_id, meal_date, meal_type)
);

-- Create custom_ingredients table for storing custom ingredients per meal
CREATE TABLE custom_ingredients (
    ingredient_id INT AUTO_INCREMENT,
    meal_id INT NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL, -- cups, tsp, lbs, oz, etc.
    notes VARCHAR(200) NULL, -- "diced", "optional", etc.
    estimated_cost DECIMAL(6,2) NULL,
    PRIMARY KEY (ingredient_id),
    FOREIGN KEY (meal_id) REFERENCES meals(meal_id) ON DELETE CASCADE,
    INDEX idx_meal_ingredients (meal_id),
    INDEX idx_ingredient_name (ingredient_name)
);
