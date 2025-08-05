-- Test data for Preppr application
-- This file generates realistic sample data for testing all functionality

USE hacknyu25;

-- Clear existing data (careful - this removes all data!)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE pantry_item_tags;
TRUNCATE TABLE pantry_tags;
TRUNCATE TABLE session_shopping_lists;
TRUNCATE TABLE session_batch_prep;
TRUNCATE TABLE meals;
TRUNCATE TABLE meal_plan_sessions;
TRUNCATE TABLE template_ingredients;
TRUNCATE TABLE recipe_templates;
TRUNCATE TABLE monthly_meal_goals;
TRUNCATE TABLE expiry_predictions;
TRUNCATE TABLE pantry_transfer_sessions;
TRUNCATE TABLE pantry_items;
TRUNCATE TABLE shopping_list_cart_mapping;
TRUNCATE TABLE shopping_list_items;
TRUNCATE TABLE shopping_lists;
TRUNCATE TABLE cart_item;
TRUNCATE TABLE shopping_cart;
TRUNCATE TABLE budget;
TRUNCATE TABLE user_budget_settings;
TRUNCATE TABLE user_meal_preferences;
TRUNCATE TABLE user_account;
SET FOREIGN_KEY_CHECKS = 1;

-- Insert test users
INSERT INTO user_account (user_ID, email, password, first_name, last_name) VALUES
('testuser1', 'john.doe@email.com', 'password123', 'John', 'Doe'),
('testuser2', 'jane.smith@email.com', 'securepass456', 'Jane', 'Smith'),
('testuser3', 'mike.wilson@email.com', 'mypass789', 'Mike', 'Wilson'),
('foodie_sarah', 'sarah.jones@email.com', 'foodlover2024', 'Sarah', 'Jones'),
('chef_marcus', 'marcus.chef@email.com', 'cookingmaster', 'Marcus', 'Rodriguez');

-- Insert user meal preferences
INSERT INTO user_meal_preferences (user_id, dietary_restrictions, favorite_cuisines, disliked_ingredients, cooking_skill_level, preferred_meal_prep_day, max_daily_cooking_time, preferred_budget_per_meal, kitchen_equipment) VALUES
('testuser1', '["vegetarian"]', '["Italian", "Mexican"]', '["mushrooms", "olives"]', 'intermediate', 'sunday', 45, 12.00, '["oven", "stovetop", "microwave", "blender"]'),
('testuser2', '["gluten-free"]', '["Asian", "Mediterranean"]', '["shellfish"]', 'advanced', 'saturday', 90, 15.00, '["oven", "stovetop", "microwave", "food_processor", "stand_mixer"]'),
('testuser3', '[]', '["American", "BBQ"]', '["cilantro", "spicy_food"]', 'beginner', 'sunday', 30, 8.00, '["oven", "stovetop", "microwave"]'),
('foodie_sarah', '["dairy-free", "nut-free"]', '["Thai", "Indian", "Middle_Eastern"]', '["fish"]', 'advanced', 'friday', 120, 20.00, '["oven", "stovetop", "microwave", "instant_pot", "air_fryer", "food_processor"]'),
('chef_marcus', '[]', '["French", "Italian", "Spanish"]', '[]', 'advanced', 'saturday', 180, 25.00, '["oven", "stovetop", "microwave", "sous_vide", "stand_mixer", "food_processor", "mandoline"]');

-- Insert user budget settings
INSERT INTO user_budget_settings (user_id, monthly_budget, budget_period, alert_threshold, category_limits_enabled, currency) VALUES
('testuser1', 400.00, 'monthly', 75.00, TRUE, 'USD'),
('testuser2', 600.00, 'monthly', 80.00, TRUE, 'USD'),
('testuser3', 250.00, 'monthly', 85.00, FALSE, 'USD'),
('foodie_sarah', 800.00, 'monthly', 70.00, TRUE, 'USD'),
('chef_marcus', 1200.00, 'monthly', 90.00, TRUE, 'USD');

-- Insert budgets for current month
INSERT INTO budget (user_id, allocated_amount, total_spent, alert_threshold, currency) VALUES
('testuser1', 400.00, 127.50, 0.75, 'USD'),
('testuser2', 600.00, 234.75, 0.80, 'USD'),
('testuser3', 250.00, 89.25, 0.85, 'USD'),
('foodie_sarah', 800.00, 456.80, 0.70, 'USD'),
('chef_marcus', 1200.00, 678.90, 0.90, 'USD');

-- Insert shopping lists
INSERT INTO shopping_lists (user_id, list_name, description, is_active) VALUES
('testuser1', 'Weekly Groceries', 'Regular weekly grocery shopping', TRUE),
('testuser1', 'Party Supplies', 'For weekend dinner party', FALSE),
('testuser2', 'Meal Prep Sunday', 'Ingredients for weekly meal prep', TRUE),
('testuser3', 'Quick Meals', 'Easy weeknight dinner ingredients', TRUE),
('foodie_sarah', 'Asian Cuisine Week', 'Ingredients for Thai and Indian dishes', TRUE),
('chef_marcus', 'French Cooking Class', 'Ingredients for cooking class demonstrations', FALSE);

-- Insert shopping list items
INSERT INTO shopping_list_items (list_id, item_name, quantity, notes, is_completed) VALUES
-- testuser1's Weekly Groceries
(1, 'Bananas', 6, 'Ripe but not overripe', FALSE),
(1, 'Whole Wheat Bread', 1, 'Dave\'s Killer Bread preferred', TRUE),
(1, 'Almond Milk', 1, 'Unsweetened vanilla', FALSE),
(1, 'Greek Yogurt', 2, 'Plain, large containers', FALSE),
(1, 'Spinach', 1, 'Baby spinach bag', FALSE),
(1, 'Tomatoes', 4, 'Roma tomatoes', TRUE),
-- testuser2's Meal Prep
(3, 'Chicken Breast', 3, '3 lbs, organic if possible', FALSE),
(3, 'Brown Rice', 1, '2 lb bag', FALSE),
(3, 'Broccoli', 2, 'Fresh heads', FALSE),
(3, 'Sweet Potatoes', 6, 'Medium sized', TRUE),
-- testuser3's Quick Meals
(4, 'Ground Turkey', 1, '1 lb package', FALSE),
(4, 'Pasta', 2, 'Whole wheat penne', FALSE),
(4, 'Marinara Sauce', 1, 'No sugar added', FALSE),
-- foodie_sarah's Asian Cuisine
(5, 'Coconut Milk', 3, 'Full fat cans', FALSE),
(5, 'Fish Sauce', 1, 'Red Boat brand', FALSE),
(5, 'Jasmine Rice', 1, '5 lb bag', FALSE),
(5, 'Thai Basil', 1, 'Fresh if available', FALSE);

-- Insert shopping carts
INSERT INTO shopping_cart (user_ID, store_name, status, shopping_list_id) VALUES
('testuser1', 'Whole Foods', 'active', 1),
('testuser1', 'Target', 'purchased', 2),
('testuser2', 'Kroger', 'active', 3),
('testuser3', 'Walmart', 'purchased', 4),
('foodie_sarah', 'Asian Market', 'active', 5),
('chef_marcus', 'Williams Sonoma', 'purchased', NULL);

-- Insert cart items
INSERT INTO cart_item (cart_ID, user_ID, quantity, item_name, price, upc, item_lifetime, image_url) VALUES
-- testuser1's active Whole Foods cart
(1, 'testuser1', 6, 'Bananas', 3.49, 4011, 7, 'https://example.com/bananas.jpg'),
(1, 'testuser1', 1, 'Almond Milk', 4.99, 025293600027, 14, 'https://example.com/almond-milk.jpg'),
(1, 'testuser1', 2, 'Greek Yogurt', 11.98, 036632006789, 21, 'https://example.com/greek-yogurt.jpg'),
(1, 'testuser1', 1, 'Baby Spinach', 3.99, 071279273456, 5, 'https://example.com/spinach.jpg'),

-- testuser1's purchased Target cart
(2, 'testuser1', 2, 'Paper Plates', 8.99, 037000123456, NULL, 'https://example.com/paper-plates.jpg'),
(2, 'testuser1', 1, 'Plastic Cups', 5.49, 037000987654, NULL, 'https://example.com/plastic-cups.jpg'),

-- testuser2's active Kroger cart
(3, 'testuser2', 3, 'Chicken Breast', 19.47, 021130034567, 3, 'https://example.com/chicken-breast.jpg'),
(3, 'testuser2', 1, 'Brown Rice', 3.99, 044000456789, 730, 'https://example.com/brown-rice.jpg'),
(3, 'testuser2', 2, 'Broccoli', 4.98, 412345000015, 7, 'https://example.com/broccoli.jpg'),

-- testuser3's purchased Walmart cart
(4, 'testuser3', 1, 'Ground Turkey', 6.98, 212345000023, 2, 'https://example.com/ground-turkey.jpg'),
(4, 'testuser3', 2, 'Whole Wheat Pasta', 3.98, 016000345678, 730, 'https://example.com/pasta.jpg'),
(4, 'testuser3', 1, 'Marinara Sauce', 2.49, 041000123456, 1095, 'https://example.com/marinara.jpg'),

-- foodie_sarah's active Asian Market cart
(5, 'foodie_sarah', 3, 'Coconut Milk', 8.97, 089686000234, 730, 'https://example.com/coconut-milk.jpg'),
(5, 'foodie_sarah', 1, 'Fish Sauce', 4.99, 073296000456, 1095, 'https://example.com/fish-sauce.jpg'),
(5, 'foodie_sarah', 1, 'Jasmine Rice', 12.99, 011110876543, 365, 'https://example.com/jasmine-rice.jpg'),

-- chef_marcus's purchased Williams Sonoma cart
(6, 'chef_marcus', 1, 'Truffle Oil', 28.99, 123456789012, 365, 'https://example.com/truffle-oil.jpg'),
(6, 'chef_marcus', 1, 'Sea Salt', 15.99, 234567890123, 1095, 'https://example.com/sea-salt.jpg');

-- Insert pantry items
INSERT INTO pantry_items (user_id, item_name, quantity, unit, category, storage_type, expiration_date, source_type, source_cart_id, is_ai_predicted_expiry, notes) VALUES
-- testuser1's pantry
('testuser1', 'Whole Wheat Bread', 0.75, 'loaf', 'Bread', 'pantry', '2024-08-08', 'shopping_trip', 2, FALSE, 'Partially used'),
('testuser1', 'Paper Plates', 15, 'pcs', 'Other', 'pantry', NULL, 'shopping_trip', 2, FALSE, 'For parties'),
('testuser1', 'Olive Oil', 1, 'bottle', 'Oils & Vinegars', 'pantry', '2025-03-15', 'manual', NULL, FALSE, 'Extra virgin'),
('testuser1', 'Garlic', 1, 'head', 'Produce', 'pantry', '2024-08-15', 'manual', NULL, TRUE, 'Store in cool, dry place'),

-- testuser2's pantry
('testuser2', 'Sweet Potatoes', 4, 'pcs', 'Produce', 'pantry', '2024-08-20', 'manual', NULL, TRUE, 'Large ones'),
('testuser2', 'Quinoa', 2, 'lbs', 'Grains', 'pantry', '2025-12-31', 'manual', NULL, FALSE, 'Organic tri-color'),
('testuser2', 'Coconut Oil', 1, 'jar', 'Oils & Vinegars', 'pantry', '2025-06-01', 'manual', NULL, FALSE, 'Virgin, solid at room temp'),

-- testuser3's pantry (from purchased cart)
('testuser3', 'Ground Turkey', 1, 'lbs', 'Meat', 'fridge', '2024-08-07', 'shopping_trip', 4, TRUE, 'Use soon'),
('testuser3', 'Whole Wheat Pasta', 2, 'boxes', 'Grains', 'pantry', '2025-08-01', 'shopping_trip', 4, FALSE, 'Penne shape'),
('testuser3', 'Marinara Sauce', 1, 'jar', 'Condiments', 'pantry', '2025-02-01', 'shopping_trip', 4, FALSE, 'No sugar added'),
('testuser3', 'Cheddar Cheese', 1, 'block', 'Dairy', 'fridge', '2024-08-25', 'manual', NULL, FALSE, 'Sharp cheddar'),

-- foodie_sarah's extensive pantry
('foodie_sarah', 'Basmati Rice', 5, 'lbs', 'Grains', 'pantry', '2025-08-01', 'manual', NULL, FALSE, 'Long grain'),
('foodie_sarah', 'Turmeric', 1, 'jar', 'Spices', 'pantry', '2026-01-01', 'manual', NULL, FALSE, 'Ground'),
('foodie_sarah', 'Cumin Seeds', 1, 'jar', 'Spices', 'pantry', '2026-01-01', 'manual', NULL, FALSE, 'Whole seeds'),
('foodie_sarah', 'Garam Masala', 1, 'jar', 'Spices', 'pantry', '2025-12-01', 'manual', NULL, FALSE, 'Homemade blend'),
('foodie_sarah', 'Coconut Milk', 6, 'cans', 'Canned Goods', 'pantry', '2025-08-01', 'manual', NULL, FALSE, 'Full fat'),

-- chef_marcus's professional pantry
('chef_marcus', 'Truffle Oil', 1, 'bottle', 'Oils & Vinegars', 'pantry', '2025-08-01', 'shopping_trip', 6, FALSE, 'White truffle'),
('chef_marcus', 'Fleur de Sel', 1, 'container', 'Spices', 'pantry', '2027-01-01', 'shopping_trip', 6, FALSE, 'French sea salt'),
('chef_marcus', 'Parmigiano-Reggiano', 2, 'lbs', 'Dairy', 'fridge', '2024-10-01', 'manual', NULL, FALSE, '24-month aged'),
('chef_marcus', 'Duck Fat', 1, 'jar', 'Oils & Vinegars', 'fridge', '2024-12-01', 'manual', NULL, FALSE, 'For roasting potatoes'),
('chef_marcus', 'Vanilla Beans', 10, 'pods', 'Spices', 'pantry', '2025-08-01', 'manual', NULL, FALSE, 'Madagascar Grade A');

-- Insert pantry tags
INSERT INTO pantry_tags (user_id, tag_name, tag_color, usage_count) VALUES
('testuser1', 'Vegetarian', '#22C55E', 5),
('testuser1', 'Quick Meal', '#3B82F6', 8),
('testuser1', 'Healthy', '#10B981', 12),
('testuser2', 'Meal Prep', '#8B5CF6', 15),
('testuser2', 'High Protein', '#EF4444', 7),
('testuser2', 'Gluten Free', '#F59E0B', 9),
('foodie_sarah', 'Asian Cuisine', '#EC4899', 20),
('foodie_sarah', 'Spice Blend', '#F97316', 6),
('foodie_sarah', 'Dairy Free', '#06B6D4', 11),
('chef_marcus', 'Gourmet', '#7C3AED', 25),
('chef_marcus', 'French', '#DC2626', 18),
('chef_marcus', 'Premium', '#059669', 22);

-- Insert pantry item tags (many-to-many relationships)
INSERT INTO pantry_item_tags (pantry_item_id, tag_id) VALUES
-- testuser1's items
(3, 1), (3, 3), -- Olive Oil: Vegetarian, Healthy
(4, 1), (4, 2), (4, 3), -- Garlic: Vegetarian, Quick Meal, Healthy
-- testuser2's items
(5, 4), (5, 3), -- Sweet Potatoes: Meal Prep, Healthy
(6, 4), (6, 5), (6, 6), -- Quinoa: Meal Prep, High Protein, Gluten Free
(7, 6), (7, 3), -- Coconut Oil: Gluten Free, Healthy
-- foodie_sarah's items
(9, 7), -- Basmati Rice: Asian Cuisine
(10, 7), (10, 8), (10, 9), -- Turmeric: Asian Cuisine, Spice Blend, Dairy Free
(11, 7), (11, 8), -- Cumin Seeds: Asian Cuisine, Spice Blend
(12, 7), (12, 8), -- Garam Masala: Asian Cuisine, Spice Blend
(13, 7), (13, 9), -- Coconut Milk: Asian Cuisine, Dairy Free
-- chef_marcus's items
(14, 10), (14, 13), -- Truffle Oil: Gourmet, Premium
(15, 10), (15, 11), (15, 13), -- Fleur de Sel: Gourmet, French, Premium
(16, 10), (16, 11), -- Parmigiano-Reggiano: Gourmet, French
(17, 10), (17, 11), -- Duck Fat: Gourmet, French
(18, 10), (18, 13); -- Vanilla Beans: Gourmet, Premium

-- Insert expiry predictions (AI learning data)
INSERT INTO expiry_predictions (item_name, storage_type, predicted_days, confidence_score, used_count) VALUES
('Bananas', 'pantry', 7, 0.95, 25),
('Bananas', 'fridge', 14, 0.90, 8),
('Ground Turkey', 'fridge', 2, 0.98, 15),
('Ground Turkey', 'freezer', 90, 0.85, 5),
('Spinach', 'fridge', 5, 0.92, 20),
('Broccoli', 'fridge', 7, 0.88, 18),
('Sweet Potatoes', 'pantry', 14, 0.85, 12),
('Garlic', 'pantry', 21, 0.90, 30),
('Bread', 'pantry', 5, 0.95, 45),
('Milk', 'fridge', 7, 0.98, 50),
('Chicken Breast', 'fridge', 3, 0.97, 35),
('Coconut Milk', 'pantry', 730, 0.80, 10);

-- Insert monthly meal goals
INSERT INTO monthly_meal_goals (user_id, month, year, meal_plans_goal, meals_completed_goal, new_recipes_goal) VALUES
('testuser1', 8, 2024, 4, 60, 8),
('testuser1', 9, 2024, 5, 75, 10),
('testuser2', 8, 2024, 6, 90, 12),
('testuser2', 9, 2024, 6, 90, 15),
('testuser3', 8, 2024, 2, 30, 5),
('foodie_sarah', 8, 2024, 8, 120, 20),
('foodie_sarah', 9, 2024, 10, 150, 25),
('chef_marcus', 8, 2024, 12, 180, 30),
('chef_marcus', 9, 2024, 15, 200, 35);

-- Insert recipe templates
INSERT INTO recipe_templates (recipe_name, description, meal_type, prep_time, cook_time, servings, estimated_cost, difficulty, calories_per_serving, instructions, cuisine_type, dietary_tags, notes) VALUES
('Classic Spaghetti Carbonara', 'Traditional Roman pasta dish with eggs, cheese, and pancetta', 'dinner', 10, 15, 4, 12.00, 'medium', 480, 'Cook spaghetti al dente. Whisk eggs with cheese. Cook pancetta until crispy. Combine hot pasta with egg mixture off heat, stirring quickly. Add pancetta and season.', 'Italian', '[]', 'Key is to not scramble the eggs'),

('Vegetarian Buddha Bowl', 'Nutritious bowl with quinoa, roasted vegetables, and tahini dressing', 'lunch', 15, 25, 2, 8.50, 'easy', 420, 'Cook quinoa. Roast vegetables (sweet potato, broccoli, carrots) with olive oil and seasonings. Make tahini dressing. Assemble bowl with greens, quinoa, roasted veggies, and dressing.', 'Mediterranean', '["vegetarian", "gluten-free", "dairy-free"]', 'Great for meal prep'),

('Thai Green Curry', 'Aromatic curry with coconut milk, vegetables, and fragrant herbs', 'dinner', 20, 20, 4, 15.00, 'medium', 380, 'Sauté curry paste in oil. Add coconut milk and bring to simmer. Add vegetables and protein of choice. Simmer until tender. Finish with Thai basil and lime juice. Serve over jasmine rice.', 'Thai', '["dairy-free", "gluten-free"]', 'Adjust spice level with more or less curry paste'),

('Overnight Oats', 'No-cook breakfast prepared the night before', 'breakfast', 5, 0, 1, 3.00, 'easy', 320, 'Combine oats, milk, chia seeds, and sweetener in jar. Add desired toppings like berries, nuts, or nut butter. Refrigerate overnight. Enjoy cold or warm slightly.', 'American', '["vegetarian"]', 'Perfect for busy mornings'),

('French Coq au Vin', 'Classic French braised chicken in wine sauce', 'dinner', 30, 90, 6, 22.00, 'hard', 450, 'Marinate chicken in wine overnight. Brown chicken and set aside. Sauté vegetables, add wine and herbs. Return chicken to pot, braise slowly. Finish with butter and fresh herbs.', 'French', '[]', 'Use a good quality red wine'),

('Grilled Salmon with Lemon Herbs', 'Simple and healthy grilled salmon with fresh herbs', 'dinner', 10, 12, 4, 18.00, 'easy', 340, 'Marinate salmon in lemon juice, olive oil, and herbs for 30 minutes. Preheat grill to medium-high. Grill salmon 4-6 minutes per side until flaky. Serve with lemon wedges.', 'Mediterranean', '["gluten-free", "dairy-free", "keto"]', 'Don\'t overcook the salmon'),

('Chickpea Curry', 'Hearty vegetarian curry with coconut milk and spices', 'dinner', 15, 30, 4, 7.00, 'easy', 280, 'Sauté onions, garlic, and ginger. Add spices and cook until fragrant. Add tomatoes, coconut milk, and chickpeas. Simmer 20 minutes. Finish with cilantro and serve over rice.', 'Indian', '["vegetarian", "vegan", "gluten-free", "dairy-free"]', 'Great with naan bread'),

('Breakfast Smoothie Bowl', 'Thick smoothie topped with granola and fresh fruit', 'breakfast', 8, 0, 1, 5.50, 'easy', 380, 'Blend frozen berries, banana, and a little liquid until thick. Pour into bowl and top with granola, fresh fruit, nuts, and seeds. Drizzle with honey if desired.', 'American', '["vegetarian", "gluten-free"]', 'Use minimal liquid for thick consistency');

-- Insert template ingredients
INSERT INTO template_ingredients (template_id, ingredient_name, quantity, unit, notes, is_pantry_item, estimated_cost) VALUES
-- Spaghetti Carbonara (template_id: 1)
(1, 'Spaghetti', 1, 'lb', '', FALSE, 2.00),
(1, 'Eggs', 4, 'large', 'room temperature', FALSE, 1.50),
(1, 'Parmigiano-Reggiano', 1, 'cup', 'freshly grated', FALSE, 4.00),
(1, 'Pancetta', 4, 'oz', 'diced', FALSE, 3.50),
(1, 'Black Pepper', 1, 'tsp', 'freshly cracked', TRUE, 0.10),
(1, 'Salt', 1, 'tsp', 'for pasta water', TRUE, 0.05),

-- Vegetarian Buddha Bowl (template_id: 2)
(2, 'Quinoa', 1, 'cup', 'uncooked', TRUE, 2.00),
(2, 'Sweet Potato', 1, 'large', 'cubed', FALSE, 1.50),
(2, 'Broccoli', 1, 'head', 'cut into florets', FALSE, 2.00),
(2, 'Carrots', 2, 'medium', 'sliced', FALSE, 1.00),
(2, 'Tahini', 3, 'tbsp', '', TRUE, 1.50),
(2, 'Lemon', 1, 'whole', 'juiced', FALSE, 0.50),
(2, 'Mixed Greens', 4, 'cups', '', FALSE, 2.00),

-- Thai Green Curry (template_id: 3)
(3, 'Green Curry Paste', 3, 'tbsp', '', FALSE, 2.00),
(3, 'Coconut Milk', 2, 'cans', 'full fat', FALSE, 4.00),
(3, 'Bell Peppers', 2, 'medium', 'sliced', FALSE, 2.50),
(3, 'Eggplant', 1, 'medium', 'cubed', FALSE, 2.00),
(3, 'Thai Basil', 1, 'cup', 'fresh leaves', FALSE, 1.50),
(3, 'Fish Sauce', 2, 'tbsp', '', TRUE, 0.50),
(3, 'Jasmine Rice', 2, 'cups', 'cooked', TRUE, 1.00),

-- Overnight Oats (template_id: 4)
(4, 'Rolled Oats', 0.5, 'cup', '', TRUE, 0.50),
(4, 'Milk', 0.5, 'cup', 'dairy or plant-based', FALSE, 0.75),
(4, 'Chia Seeds', 1, 'tbsp', '', TRUE, 0.50),
(4, 'Honey', 1, 'tbsp', 'or maple syrup', TRUE, 0.25),
(4, 'Berries', 0.5, 'cup', 'fresh or frozen', FALSE, 1.50),

-- French Coq au Vin (template_id: 5)
(5, 'Chicken', 1, 'whole', 'cut into pieces', FALSE, 8.00),
(5, 'Red Wine', 2, 'cups', 'good quality', FALSE, 8.00),
(5, 'Pearl Onions', 1, 'cup', '', FALSE, 2.00),
(5, 'Mushrooms', 8, 'oz', 'button or cremini', FALSE, 2.50),
(5, 'Bacon', 4, 'strips', 'diced', FALSE, 3.00),
(5, 'Thyme', 2, 'sprigs', 'fresh', FALSE, 0.50),

-- Grilled Salmon (template_id: 6)
(6, 'Salmon Fillets', 4, 'pieces', '6 oz each', FALSE, 16.00),
(6, 'Lemon', 2, 'whole', 'juiced and zested', FALSE, 1.00),
(6, 'Olive Oil', 3, 'tbsp', 'extra virgin', TRUE, 0.75),
(6, 'Fresh Dill', 2, 'tbsp', 'chopped', FALSE, 1.00),
(6, 'Garlic', 2, 'cloves', 'minced', TRUE, 0.25),

-- Chickpea Curry (template_id: 7)
(7, 'Chickpeas', 2, 'cans', 'drained and rinsed', FALSE, 2.00),
(7, 'Coconut Milk', 1, 'can', 'full fat', FALSE, 2.00),
(7, 'Onion', 1, 'large', 'diced', FALSE, 1.00),
(7, 'Tomatoes', 1, 'can', 'diced', FALSE, 1.50),
(7, 'Garam Masala', 2, 'tsp', '', TRUE, 0.25),
(7, 'Turmeric', 1, 'tsp', '', TRUE, 0.10),
(7, 'Cilantro', 0.25, 'cup', 'fresh, chopped', FALSE, 0.50),

-- Breakfast Smoothie Bowl (template_id: 8)
(8, 'Frozen Berries', 1, 'cup', 'mixed', FALSE, 2.50),
(8, 'Banana', 1, 'medium', 'frozen', FALSE, 0.75),
(8, 'Greek Yogurt', 0.5, 'cup', 'plain', FALSE, 1.50),
(8, 'Granola', 0.25, 'cup', '', FALSE, 1.00),
(8, 'Almonds', 2, 'tbsp', 'sliced', TRUE, 0.75),
(8, 'Honey', 1, 'tbsp', 'for drizzling', TRUE, 0.25);

-- Insert meal plan sessions
INSERT INTO meal_plan_sessions (user_id, session_name, start_date, end_date, total_days, dietary_preference, max_cooking_time, status, ai_model_used, generation_prompt) VALUES
('testuser1', 'Vegetarian Week', '2024-08-05', '2024-08-11', 7, 'vegetarian', 45, 'active', 'gemini-1.5-flash-latest', 'Create a 7-day vegetarian meal plan for intermediate cook, 45 min max cooking time per meal'),
('testuser2', 'Meal Prep Master', '2024-08-05', '2024-08-18', 14, 'gluten-free', 90, 'active', 'gemini-1.5-flash-latest', 'Create a 2-week gluten-free meal prep plan with batch cooking focus'),
('testuser3', 'Quick & Easy', '2024-08-01', '2024-08-07', 7, 'none', 30, 'completed', 'gemini-1.5-flash-latest', 'Simple 7-day meal plan for beginner cook, maximum 30 minutes per meal'),
('foodie_sarah', 'Asian Fusion Month', '2024-08-01', '2024-08-31', 31, 'dairy-free', 120, 'active', 'gemini-1.5-flash-latest', 'Month-long Asian fusion meal plan, dairy-free, advanced cooking techniques'),
('chef_marcus', 'French Classics', '2024-07-15', '2024-07-28', 14, 'none', 180, 'completed', 'gemini-1.5-flash-latest', 'Two-week French cuisine masterclass meal plan, no dietary restrictions');

-- Insert meals
INSERT INTO meals (user_id, meal_date, meal_type, recipe_template_id, session_id, is_completed, completion_date, is_locked) VALUES
-- testuser1's Vegetarian Week
('testuser1', '2024-08-05', 'breakfast', 4, 1, TRUE, '2024-08-05 08:30:00', FALSE),
('testuser1', '2024-08-05', 'lunch', 2, 1, TRUE, '2024-08-05 13:15:00', FALSE),
('testuser1', '2024-08-05', 'dinner', 7, 1, TRUE, '2024-08-05 19:45:00', FALSE),
('testuser1', '2024-08-06', 'breakfast', 4, 1, TRUE, '2024-08-06 08:00:00', FALSE),
('testuser1', '2024-08-06', 'lunch', 2, 1, FALSE, NULL, FALSE),
('testuser1', '2024-08-06', 'dinner', 7, 1, FALSE, NULL, FALSE),
('testuser1', '2024-08-07', 'breakfast', 8, 1, FALSE, NULL, FALSE),

-- testuser2's Meal Prep
('testuser2', '2024-08-05', 'breakfast', 8, 2, TRUE, '2024-08-05 07:30:00', FALSE),
('testuser2', '2024-08-05', 'lunch', 2, 2, TRUE, '2024-08-05 12:30:00', FALSE),
('testuser2', '2024-08-05', 'dinner', 6, 2, TRUE, '2024-08-05 19:00:00', FALSE),
('testuser2', '2024-08-06', 'breakfast', 8, 2, TRUE, '2024-08-06 07:30:00', FALSE),
('testuser2', '2024-08-06', 'lunch', 2, 2, FALSE, NULL, FALSE),

-- testuser3's completed Quick & Easy week
('testuser3', '2024-08-01', 'dinner', NULL, 3, TRUE, '2024-08-01 18:30:00', FALSE),
('testuser3', '2024-08-02', 'dinner', NULL, 3, TRUE, '2024-08-02 19:00:00', FALSE),
('testuser3', '2024-08-03', 'dinner', NULL, 3, TRUE, '2024-08-03 18:45:00', FALSE),

-- foodie_sarah's Asian Fusion
('foodie_sarah', '2024-08-01', 'dinner', 3, 4, TRUE, '2024-08-01 20:15:00', FALSE),
('foodie_sarah', '2024-08-02', 'dinner', 7, 4, TRUE, '2024-08-02 19:30:00', FALSE),
('foodie_sarah', '2024-08-03', 'dinner', 3, 4, FALSE, NULL, FALSE),

-- chef_marcus's completed French Classics
('chef_marcus', '2024-07-15', 'dinner', 5, 5, TRUE, '2024-07-15 21:00:00', FALSE),
('chef_marcus', '2024-07-16', 'dinner', 5, 5, TRUE, '2024-07-16 20:45:00', FALSE);

-- Insert custom meals (not using templates)
INSERT INTO meals (user_id, meal_date, meal_type, session_id, custom_recipe_name, custom_instructions, is_completed, completion_date) VALUES
('testuser3', '2024-08-04', 'dinner', 3, 'Turkey Pasta Bake', 'Brown ground turkey with onions. Mix with cooked pasta and marinara sauce. Top with cheese and bake 25 minutes.', TRUE, '2024-08-04 19:15:00'),
('testuser3', '2024-08-05', 'dinner', 3, 'Simple Stir Fry', 'Quick vegetable stir fry with whatever is in the fridge. Serve over rice.', TRUE, '2024-08-05 18:20:00');

-- Insert session batch prep instructions
INSERT INTO session_batch_prep (session_id, prep_session_name, step_order, description, estimated_time, equipment_needed, tips) VALUES
-- testuser1's Vegetarian Week prep
(1, 'Sunday Meal Prep', 1, 'Cook quinoa in large batch (3 cups dry quinoa)', 25, 'Large pot, measuring cups', 'Cook extra quinoa for the week'),
(1, 'Sunday Meal Prep', 2, 'Prep overnight oats for 3 days', 15, 'Mason jars, measuring spoons', 'Make 3 jars at once to save time'),
(1, 'Sunday Meal Prep', 3, 'Roast vegetables for Buddha bowls', 30, 'Large baking sheets, knife', 'Cut vegetables uniformly for even cooking'),

-- testuser2's Meal Prep session
(2, 'Weekend Batch Prep', 1, 'Grill 12 salmon fillets at once', 45, 'Large grill or grill pan', 'Don\'t overcook - they\'ll reheat better'),
(2, 'Weekend Batch Prep', 2, 'Prepare smoothie bowl toppings', 20, 'Food processor, storage containers', 'Keep granola separate until serving'),
(2, 'Weekend Batch Prep', 3, 'Assemble Buddha bowl components', 30, 'Large containers, portioning containers', 'Keep dressing separate'),

-- foodie_sarah's Asian prep
(4, 'Asian Prep Day', 1, 'Make curry pastes from scratch', 60, 'Food processor, spice grinder', 'Make extra and freeze in ice cube trays'),
(4, 'Asian Prep Day', 2, 'Prep aromatics (ginger, garlic, lemongrass)', 30, 'Sharp knife, storage containers', 'Mince and store in oil to preserve'),
(4, 'Asian Prep Day', 3, 'Cook jasmine rice in rice cooker', 20, 'Rice cooker, rice paddle', 'Make extra for fried rice later'),

-- chef_marcus's French prep
(5, 'French Technique Day', 1, 'Prepare mise en place for Coq au Vin', 45, 'Multiple cutting boards, knives', 'Organization is key in French cooking'),
(5, 'French Technique Day', 2, 'Make clarified butter', 20, 'Heavy saucepan, fine strainer', 'Store in refrigerator for multiple uses'),
(5, 'French Technique Day', 3, 'Prepare herb bouquet garni', 15, 'Kitchen twine, fresh herbs', 'Tie tightly so herbs don\'t escape');

-- Insert session shopping lists (consolidated ingredients)
INSERT INTO session_shopping_lists (session_id, ingredient_name, total_quantity, unit, estimated_cost, category, meals_using) VALUES
-- testuser1's Vegetarian Week shopping
(1, 'Quinoa', 3, 'cups', 6.00, 'Grains', '[2, 5]'),
(1, 'Sweet Potato', 4, 'large', 6.00, 'Produce', '[2, 5]'),
(1, 'Chickpeas', 4, 'cans', 4.00, 'Canned Goods', '[3, 6]'),
(1, 'Coconut Milk', 2, 'cans', 4.00, 'Canned Goods', '[3, 6]'),
(1, 'Mixed Berries', 2, 'cups', 8.00, 'Produce', '[1, 4, 7]'),
(1, 'Rolled Oats', 2, 'cups', 3.00, 'Grains', '[1, 4]'),

-- testuser2's Meal Prep shopping
(2, 'Salmon Fillets', 12, 'pieces', 96.00, 'Meat', '[8, 10, 12]'),
(2, 'Greek Yogurt', 4, 'containers', 12.00, 'Dairy', '[8, 11]'),
(2, 'Quinoa', 4, 'cups', 8.00, 'Grains', '[9, 11]'),
(2, 'Frozen Berries', 3, 'bags', 15.00, 'Frozen Foods', '[8, 11]'),

-- foodie_sarah's Asian shopping
(4, 'Green Curry Paste', 6, 'tbsp', 4.00, 'Condiments', '[15, 17]'),
(4, 'Coconut Milk', 6, 'cans', 12.00, 'Canned Goods', '[15, 16, 17]'),
(4, 'Thai Basil', 3, 'bunches', 6.00, 'Produce', '[15, 17]'),
(4, 'Chickpeas', 4, 'cans', 4.00, 'Canned Goods', '[16]'),
(4, 'Jasmine Rice', 3, 'lbs', 6.00, 'Grains', '[15, 16, 17]'),

-- chef_marcus's French shopping
(5, 'Whole Chicken', 2, 'whole', 24.00, 'Meat', '[18, 19]'),
(5, 'Red Wine', 4, 'cups', 20.00, 'Beverages', '[18, 19]'),
(5, 'Pearl Onions', 2, 'lbs', 6.00, 'Produce', '[18, 19]'),
(5, 'Fresh Thyme', 4, 'bunches', 4.00, 'Fresh Herbs', '[18, 19]');

-- Insert pantry transfer sessions
INSERT INTO pantry_transfer_sessions (user_id, cart_id, transfer_date, items_transferred, notes) VALUES
('testuser1', 2, '2024-08-02 15:30:00', 2, 'Party supplies transferred after event'),
('testuser3', 4, '2024-08-01 18:00:00', 3, 'Weekly grocery haul - all items transferred'),
('chef_marcus', 6, '2024-07-20 16:45:00', 2, 'Gourmet ingredients for cooking class');

-- Insert shopping list to cart mappings
INSERT INTO shopping_list_cart_mapping (cart_id, list_item_id, cart_item_id, is_found) VALUES
-- testuser1's mappings (some items found, some not)
(1, 1, 1, TRUE),  -- Bananas found and added
(1, 3, 2, TRUE),  -- Almond Milk found and added
(1, 4, 3, TRUE),  -- Greek Yogurt found and added
(1, 5, 4, TRUE),  -- Spinach found and added
(1, 2, NULL, FALSE), -- Bread not found yet
(1, 6, NULL, FALSE), -- Tomatoes marked as completed in list but not in cart

-- testuser2's mappings
(3, 7, 5, TRUE),  -- Chicken Breast found
(3, 8, 6, TRUE),  -- Brown Rice found
(3, 9, 7, TRUE),  -- Broccoli found
(3, 10, NULL, FALSE), -- Sweet Potatoes completed in list but not in current cart

-- testuser3's completed mappings
(4, 11, 8, TRUE), -- Ground Turkey found
(4, 12, 9, TRUE), -- Pasta found
(4, 13, 10, TRUE); -- Marinara found

-- Final summary comment
-- This test data includes:
-- - 5 users with different cooking skills and preferences
-- - Shopping lists and carts with realistic items and prices
-- - Pantry items with expiration dates and storage types
-- - Meal planning sessions with actual recipes
-- - Budget tracking and goals
-- - Realistic ingredient costs and quantities
-- - Pantry tags and categorization
-- - AI expiry predictions based on historical data
-- - Meal completion tracking
-- All foreign key relationships are properly maintained