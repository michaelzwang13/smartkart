-- Meal Plan Generator Database Schema
-- Add these tables to the existing database

USE hacknyu25;

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

-- Insert some common dietary preferences for reference
INSERT INTO pantry_categories (category_name, default_storage_type, typical_shelf_life_days) VALUES
('Fresh Herbs', 'fridge', 7),
('Oils & Vinegars', 'pantry', 365),
('Baking Supplies', 'pantry', 180)
ON DUPLICATE KEY UPDATE category_name = VALUES(category_name);