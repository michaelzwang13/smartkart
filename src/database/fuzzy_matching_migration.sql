-- Migration to add fuzzy matching tables for ingredient-pantry matching
USE hacknyu25;

-- Create table to store fuzzy matching results to improve performance over time
CREATE TABLE ingredient_pantry_matches (
    match_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    pantry_item_name VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL, -- 0.00 to 100.00
    match_type ENUM('auto', 'confirm', 'missing') NOT NULL,
    is_user_confirmed BOOLEAN DEFAULT FALSE, -- if user manually confirmed this match
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INT DEFAULT 1,
    PRIMARY KEY (match_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID) ON DELETE CASCADE,
    INDEX idx_user_matches (user_id),
    INDEX idx_ingredient_name (ingredient_name),
    INDEX idx_pantry_name (pantry_item_name),
    INDEX idx_confidence (confidence_score),
    INDEX idx_match_type (match_type),
    -- Prevent duplicate matches for same user/ingredient/pantry combination
    UNIQUE KEY unique_user_ingredient_pantry (user_id, ingredient_name, pantry_item_name)
);

-- Create table to store user feedback on fuzzy matches to improve future matching
CREATE TABLE fuzzy_match_feedback (
    feedback_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    suggested_pantry_item VARCHAR(100) NULL, -- what the system suggested
    actual_pantry_item VARCHAR(100) NULL, -- what the user actually selected
    action_taken ENUM('accepted', 'rejected', 'corrected', 'ignored') NOT NULL,
    original_confidence DECIMAL(5,2) NULL,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_context VARCHAR(50) NULL, -- meal_plan, shopping_list, etc.
    PRIMARY KEY (feedback_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID) ON DELETE CASCADE,
    INDEX idx_user_feedback (user_id),
    INDEX idx_ingredient_feedback (ingredient_name),
    INDEX idx_action_taken (action_taken),
    INDEX idx_feedback_date (feedback_date)
);

-- Create table to store pre-computed fuzzy match suggestions for better performance
CREATE TABLE ingredient_match_suggestions (
    suggestion_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    suggested_matches TEXT NOT NULL, -- JSON array of {pantry_item_name, confidence_score, match_type}
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL, -- cache expiration (e.g., when pantry changes significantly)
    is_stale BOOLEAN DEFAULT FALSE, -- mark as stale when pantry is updated
    PRIMARY KEY (suggestion_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID) ON DELETE CASCADE,
    INDEX idx_user_suggestions (user_id),
    INDEX idx_ingredient_suggestions (ingredient_name),
    INDEX idx_computed_at (computed_at),
    INDEX idx_expires_at (expires_at),
    -- Prevent duplicate suggestions for same user/ingredient
    UNIQUE KEY unique_user_ingredient_suggestion (user_id, ingredient_name)
);

-- Create table to track shopping list generation sessions with fuzzy matching
CREATE TABLE shopping_generation_sessions (
    generation_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    meal_plan_session_id INT NULL, -- if generated from meal plan
    generation_type ENUM('meal_plan', 'manual', 'recipe') NOT NULL,
    total_ingredients INT DEFAULT 0,
    auto_matched_count INT DEFAULT 0,
    confirm_needed_count INT DEFAULT 0,
    missing_count INT DEFAULT 0,
    user_reviewed BOOLEAN DEFAULT FALSE,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    notes TEXT NULL,
    PRIMARY KEY (generation_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID) ON DELETE CASCADE,
    FOREIGN KEY (meal_plan_session_id) REFERENCES meal_plan_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_user_generations (user_id),
    INDEX idx_generation_type (generation_type),
    INDEX idx_meal_plan_generations (meal_plan_session_id),
    INDEX idx_generated_at (generated_at)
);

-- Create table to store detailed ingredient matching results for each generation session
CREATE TABLE generation_ingredient_matches (
    match_result_id INT AUTO_INCREMENT,
    generation_id INT NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    required_quantity DECIMAL(10,2) NOT NULL,
    required_unit VARCHAR(20) NOT NULL,
    pantry_item_id INT NULL, -- matched pantry item (if any)
    pantry_available_quantity DECIMAL(10,2) NULL,
    match_confidence DECIMAL(5,2) NULL,
    match_type ENUM('auto', 'confirm', 'missing', 'user_override') NOT NULL,
    is_user_confirmed BOOLEAN DEFAULT FALSE,
    needs_to_buy_quantity DECIMAL(10,2) DEFAULT 0.00, -- how much still needed after pantry check
    estimated_cost DECIMAL(8,2) NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (match_result_id),
    FOREIGN KEY (generation_id) REFERENCES shopping_generation_sessions(generation_id) ON DELETE CASCADE,
    FOREIGN KEY (pantry_item_id) REFERENCES pantry_items(pantry_item_id) ON DELETE SET NULL,
    INDEX idx_generation_matches (generation_id),
    INDEX idx_ingredient_match_name (ingredient_name),
    INDEX idx_pantry_item_match (pantry_item_id),
    INDEX idx_match_type_result (match_type),
    -- Prevent duplicate ingredient matches per generation
    UNIQUE KEY unique_generation_ingredient (generation_id, ingredient_name, required_unit)
);

-- Create indexes for performance optimization on existing tables
CREATE INDEX idx_pantry_item_name ON pantry_items(item_name);
CREATE INDEX idx_template_ingredient_name ON template_ingredients(ingredient_name);
CREATE INDEX idx_session_shopping_ingredient ON session_shopping_lists(ingredient_name);

-- Add trigger to mark match suggestions as stale when pantry items are modified
DELIMITER //
CREATE TRIGGER pantry_update_stale_suggestions
    AFTER UPDATE ON pantry_items
    FOR EACH ROW
BEGIN
    -- Mark suggestions as stale when pantry item name changes or item is consumed
    IF OLD.item_name != NEW.item_name OR OLD.is_consumed != NEW.is_consumed THEN
        UPDATE ingredient_match_suggestions 
        SET is_stale = TRUE 
        WHERE user_id = NEW.user_id;
    END IF;
END//

CREATE TRIGGER pantry_insert_stale_suggestions
    AFTER INSERT ON pantry_items
    FOR EACH ROW
BEGIN
    -- Mark suggestions as stale when new pantry items are added
    UPDATE ingredient_match_suggestions 
    SET is_stale = TRUE 
    WHERE user_id = NEW.user_id;
END//

CREATE TRIGGER pantry_delete_stale_suggestions
    AFTER DELETE ON pantry_items
    FOR EACH ROW
BEGIN
    -- Mark suggestions as stale when pantry items are deleted
    UPDATE ingredient_match_suggestions 
    SET is_stale = TRUE 
    WHERE user_id = OLD.user_id;
END//
DELIMITER ;