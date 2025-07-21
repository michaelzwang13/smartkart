-- Test data for spending trends chart
-- This file contains fake data to test the budget spending trends functionality

USE hacknyu25;

-- First, let's insert some test users if they don't exist
INSERT IGNORE INTO user_account (user_ID, email, password) VALUES
('test_user_1', 'test1@example.com', 'password123'),
('test_user_2', 'test2@example.com', 'password123');

-- Insert shopping carts with various dates for testing different periods
-- Last 7 days data (7D period)
INSERT INTO shopping_cart (cart_ID, user_ID, store_name, status, created_at) VALUES
-- Today
(101, 'test_user_1', 'Walmart', 'purchased', NOW()),
-- Yesterday
(102, 'test_user_1', 'Target', 'purchased', DATE_SUB(NOW(), INTERVAL 1 DAY)),
-- 2 days ago
(103, 'test_user_1', 'Costco', 'purchased', DATE_SUB(NOW(), INTERVAL 2 DAY)),
-- 3 days ago  
(104, 'test_user_1', 'Kroger', 'purchased', DATE_SUB(NOW(), INTERVAL 3 DAY)),
-- 5 days ago
(105, 'test_user_1', 'Whole Foods', 'purchased', DATE_SUB(NOW(), INTERVAL 5 DAY)),
-- 6 days ago
(106, 'test_user_1', 'Safeway', 'purchased', DATE_SUB(NOW(), INTERVAL 6 DAY));

-- Last month data (1M period)
INSERT INTO shopping_cart (cart_ID, user_ID, store_name, status, created_at) VALUES
-- Week 1
(107, 'test_user_1', 'Walmart', 'purchased', DATE_SUB(NOW(), INTERVAL 8 DAY)),
(108, 'test_user_1', 'Target', 'purchased', DATE_SUB(NOW(), INTERVAL 10 DAY)),
-- Week 2  
(109, 'test_user_1', 'Costco', 'purchased', DATE_SUB(NOW(), INTERVAL 15 DAY)),
(110, 'test_user_1', 'Kroger', 'purchased', DATE_SUB(NOW(), INTERVAL 17 DAY)),
-- Week 3
(111, 'test_user_1', 'Whole Foods', 'purchased', DATE_SUB(NOW(), INTERVAL 22 DAY)),
(112, 'test_user_1', 'Safeway', 'purchased', DATE_SUB(NOW(), INTERVAL 24 DAY)),
-- Week 4
(113, 'test_user_1', 'Walmart', 'purchased', DATE_SUB(NOW(), INTERVAL 29 DAY)),
(114, 'test_user_1', 'Target', 'purchased', DATE_SUB(NOW(), INTERVAL 31 DAY));

-- Last 3 months data (3M period)
INSERT INTO shopping_cart (cart_ID, user_ID, store_name, status, created_at) VALUES
-- Month 2 (various weeks)
(115, 'test_user_1', 'Costco', 'purchased', DATE_SUB(NOW(), INTERVAL 35 DAY)),
(116, 'test_user_1', 'Kroger', 'purchased', DATE_SUB(NOW(), INTERVAL 42 DAY)),
(117, 'test_user_1', 'Whole Foods', 'purchased', DATE_SUB(NOW(), INTERVAL 49 DAY)),
(118, 'test_user_1', 'Safeway', 'purchased', DATE_SUB(NOW(), INTERVAL 56 DAY)),
-- Month 3 (various weeks)
(119, 'test_user_1', 'Walmart', 'purchased', DATE_SUB(NOW(), INTERVAL 63 DAY)),
(120, 'test_user_1', 'Target', 'purchased', DATE_SUB(NOW(), INTERVAL 70 DAY)),
(121, 'test_user_1', 'Costco', 'purchased', DATE_SUB(NOW(), INTERVAL 77 DAY)),
(122, 'test_user_1', 'Kroger', 'purchased', DATE_SUB(NOW(), INTERVAL 84 DAY));

-- Last year data (1Y period) - spread across months
INSERT INTO shopping_cart (cart_ID, user_ID, store_name, status, created_at) VALUES
-- 2 months ago
(123, 'test_user_1', 'Whole Foods', 'purchased', DATE_SUB(NOW(), INTERVAL 2 MONTH)),
(124, 'test_user_1', 'Safeway', 'purchased', DATE_SUB(NOW(), INTERVAL 2 MONTH)),
-- 3 months ago
(125, 'test_user_1', 'Walmart', 'purchased', DATE_SUB(NOW(), INTERVAL 3 MONTH)),
(126, 'test_user_1', 'Target', 'purchased', DATE_SUB(NOW(), INTERVAL 3 MONTH)),
-- 4 months ago
(127, 'test_user_1', 'Costco', 'purchased', DATE_SUB(NOW(), INTERVAL 4 MONTH)),
-- 5 months ago
(128, 'test_user_1', 'Kroger', 'purchased', DATE_SUB(NOW(), INTERVAL 5 MONTH)),
-- 6 months ago
(129, 'test_user_1', 'Whole Foods', 'purchased', DATE_SUB(NOW(), INTERVAL 6 MONTH)),
-- 8 months ago
(130, 'test_user_1', 'Safeway', 'purchased', DATE_SUB(NOW(), INTERVAL 8 MONTH)),
-- 10 months ago
(131, 'test_user_1', 'Walmart', 'purchased', DATE_SUB(NOW(), INTERVAL 10 MONTH)),
-- 11 months ago
(132, 'test_user_1', 'Target', 'purchased', DATE_SUB(NOW(), INTERVAL 11 MONTH));

-- Now insert cart items with varying amounts to create realistic spending data
-- 7D period items (recent days)
INSERT INTO cart_item (item_ID, cart_ID, user_ID, quantity, item_name, price, upc, item_lifetime, image_url) VALUES
-- Today's shopping ($85.50)
(201, 101, 'test_user_1', 2, 'Milk', 4.99, 12345, 7, 'https://example.com/milk.jpg'),
(202, 101, 'test_user_1', 1, 'Bread', 3.49, 12346, 5, 'https://example.com/bread.jpg'),
(203, 101, 'test_user_1', 3, 'Chicken Breast', 25.67, 12347, 3, 'https://example.com/chicken.jpg'),
(204, 101, 'test_user_1', 1, 'Cheese', 8.99, 12348, 14, 'https://example.com/cheese.jpg'),
(205, 101, 'test_user_1', 2, 'Yogurt', 6.49, 12349, 10, 'https://example.com/yogurt.jpg'),
(206, 101, 'test_user_1', 1, 'Bananas', 2.99, 12350, 5, 'https://example.com/banana.jpg'),
(207, 101, 'test_user_1', 1, 'Pasta Sauce', 3.79, 12351, 365, 'https://example.com/sauce.jpg'),
(208, 101, 'test_user_1', 1, 'Pasta', 1.99, 12352, 730, 'https://example.com/pasta.jpg'),
(209, 101, 'test_user_1', 1, 'Orange Juice', 4.29, 12353, 7, 'https://example.com/oj.jpg'),
(210, 101, 'test_user_1', 1, 'Eggs', 3.89, 12354, 21, 'https://example.com/eggs.jpg'),
(211, 101, 'test_user_1', 1, 'Apples', 5.99, 12355, 14, 'https://example.com/apple.jpg'),
(212, 101, 'test_user_1', 1, 'Ground Beef', 12.99, 12356, 2, 'https://example.com/beef.jpg'),
(213, 101, 'test_user_1', 1, 'Cereal', 4.99, 12357, 365, 'https://example.com/cereal.jpg'),

-- Yesterday's shopping ($62.30)
(214, 102, 'test_user_1', 1, 'Salmon', 18.99, 12358, 2, 'https://example.com/salmon.jpg'),
(215, 102, 'test_user_1', 2, 'Broccoli', 3.99, 12359, 7, 'https://example.com/broccoli.jpg'),
(216, 102, 'test_user_1', 1, 'Rice', 4.99, 12360, 730, 'https://example.com/rice.jpg'),
(217, 102, 'test_user_1', 1, 'Bell Peppers', 5.49, 12361, 10, 'https://example.com/peppers.jpg'),
(218, 102, 'test_user_1', 1, 'Onions', 2.99, 12362, 30, 'https://example.com/onion.jpg'),
(219, 102, 'test_user_1', 1, 'Garlic', 1.99, 12363, 30, 'https://example.com/garlic.jpg'),
(220, 102, 'test_user_1', 1, 'Tomatoes', 4.99, 12364, 7, 'https://example.com/tomato.jpg'),
(221, 102, 'test_user_1', 1, 'Lettuce', 2.99, 12365, 7, 'https://example.com/lettuce.jpg'),
(222, 102, 'test_user_1', 1, 'Carrots', 2.49, 12366, 14, 'https://example.com/carrot.jpg'),
(223, 102, 'test_user_1', 1, 'Potatoes', 3.99, 12367, 30, 'https://example.com/potato.jpg'),
(224, 102, 'test_user_1', 1, 'Spinach', 3.49, 12368, 5, 'https://example.com/spinach.jpg'),
(225, 102, 'test_user_1', 1, 'Mushrooms', 4.99, 12369, 7, 'https://example.com/mushroom.jpg'),

-- 2 days ago ($45.75)
(226, 103, 'test_user_1', 1, 'Steak', 22.99, 12370, 3, 'https://example.com/steak.jpg'),
(227, 103, 'test_user_1', 1, 'Sweet Potatoes', 3.99, 12371, 14, 'https://example.com/sweetpotato.jpg'),
(228, 103, 'test_user_1', 1, 'Avocados', 4.99, 12372, 5, 'https://example.com/avocado.jpg'),
(229, 103, 'test_user_1', 1, 'Lemons', 2.99, 12373, 14, 'https://example.com/lemon.jpg'),
(230, 103, 'test_user_1', 1, 'Cucumbers', 2.49, 12374, 7, 'https://example.com/cucumber.jpg'),
(231, 103, 'test_user_1', 1, 'Green Beans', 3.99, 12375, 7, 'https://example.com/greenbeans.jpg'),
(232, 103, 'test_user_1', 1, 'Zucchini', 2.99, 12376, 7, 'https://example.com/zucchini.jpg'),
(233, 103, 'test_user_1', 1, 'Corn', 1.50, 12377, 7, 'https://example.com/corn.jpg'),

-- 3 days ago ($73.20)
(234, 104, 'test_user_1', 1, 'Pork Chops', 15.99, 12378, 3, 'https://example.com/pork.jpg'),
(235, 104, 'test_user_1', 1, 'Turkey', 12.99, 12379, 3, 'https://example.com/turkey.jpg'),
(236, 104, 'test_user_1', 2, 'Frozen Pizza', 8.99, 12380, 180, 'https://example.com/pizza.jpg'),
(237, 104, 'test_user_1', 1, 'Ice Cream', 6.99, 12381, 90, 'https://example.com/icecream.jpg'),
(238, 104, 'test_user_1', 1, 'Chips', 4.49, 12382, 60, 'https://example.com/chips.jpg'),
(239, 104, 'test_user_1', 1, 'Soda', 5.99, 12383, 120, 'https://example.com/soda.jpg'),
(240, 104, 'test_user_1', 1, 'Crackers', 3.99, 12384, 120, 'https://example.com/crackers.jpg'),
(241, 104, 'test_user_1', 1, 'Peanut Butter', 4.99, 12385, 365, 'https://example.com/pb.jpg'),
(242, 104, 'test_user_1', 1, 'Jelly', 3.49, 12386, 365, 'https://example.com/jelly.jpg'),
(243, 104, 'test_user_1', 1, 'Coffee', 9.99, 12387, 365, 'https://example.com/coffee.jpg'),

-- 5 days ago ($38.95)
(244, 105, 'test_user_1', 1, 'Shrimp', 14.99, 12388, 2, 'https://example.com/shrimp.jpg'),
(245, 105, 'test_user_1', 1, 'Asparagus', 4.99, 12389, 7, 'https://example.com/asparagus.jpg'),
(246, 105, 'test_user_1', 1, 'Strawberries', 5.99, 12390, 5, 'https://example.com/strawberry.jpg'),
(247, 105, 'test_user_1', 1, 'Blueberries', 6.99, 12391, 7, 'https://example.com/blueberry.jpg'),
(248, 105, 'test_user_1', 1, 'Grapes', 5.99, 12392, 7, 'https://example.com/grapes.jpg'),

-- 6 days ago ($91.40)
(249, 106, 'test_user_1', 1, 'Lobster', 29.99, 12393, 1, 'https://example.com/lobster.jpg'),
(250, 106, 'test_user_1', 1, 'Crab', 19.99, 12394, 1, 'https://example.com/crab.jpg'),
(251, 106, 'test_user_1', 1, 'Scallops', 24.99, 12395, 2, 'https://example.com/scallop.jpg'),
(252, 106, 'test_user_1', 1, 'Wine', 16.99, 12396, 1095, 'https://example.com/wine.jpg');

-- Add items for older periods with varying amounts
-- Week 2 data (1M period)
INSERT INTO cart_item (item_ID, cart_ID, user_ID, quantity, item_name, price, upc, item_lifetime, image_url) VALUES
(253, 107, 'test_user_1', 3, 'Chicken Thighs', 18.99, 12397, 3, 'https://example.com/thigh.jpg'),
(254, 107, 'test_user_1', 2, 'Ground Turkey', 12.99, 12398, 2, 'https://example.com/gturkey.jpg'),
(255, 107, 'test_user_1', 1, 'Olive Oil', 8.99, 12399, 730, 'https://example.com/oil.jpg'),

(256, 108, 'test_user_1', 5, 'Canned Tomatoes', 12.45, 12400, 730, 'https://example.com/ctomato.jpg'),
(257, 108, 'test_user_1', 1, 'Parmesan', 9.99, 12401, 60, 'https://example.com/parm.jpg'),
(258, 108, 'test_user_1', 2, 'Garlic Bread', 5.98, 12402, 7, 'https://example.com/gbread.jpg'),

-- Month 2-3 data (3M period)
(259, 115, 'test_user_1', 1, 'Whole Chicken', 8.99, 12403, 3, 'https://example.com/wchicken.jpg'),
(260, 115, 'test_user_1', 1, 'Butter', 4.99, 12404, 30, 'https://example.com/butter.jpg'),

(261, 119, 'test_user_1', 2, 'Bacon', 14.99, 12405, 7, 'https://example.com/bacon.jpg'),
(262, 119, 'test_user_1', 1, 'Sausage', 6.99, 12406, 14, 'https://example.com/sausage.jpg'),

-- Year data (1Y period) - spread across months
(263, 123, 'test_user_1', 1, 'Prime Rib', 45.99, 12407, 3, 'https://example.com/rib.jpg'),
(264, 125, 'test_user_1', 2, 'Lamb Chops', 32.99, 12408, 3, 'https://example.com/lamb.jpg'),
(265, 127, 'test_user_1', 1, 'Duck', 28.99, 12409, 3, 'https://example.com/duck.jpg'),
(266, 129, 'test_user_1', 1, 'Venison', 39.99, 12410, 3, 'https://example.com/venison.jpg'),
(267, 131, 'test_user_1', 1, 'Caviar', 89.99, 12411, 30, 'https://example.com/caviar.jpg');

-- Add some budget settings for the test user
INSERT IGNORE INTO user_budget_settings (user_id, monthly_budget, budget_period, alert_threshold, category_limits_enabled) VALUES
('test_user_1', 1500.00, 'monthly', 85.00, TRUE);

-- Add current month budget entry
INSERT IGNORE INTO budget (user_id, allocated_amount, total_spent, alert_threshold) VALUES
('test_user_1', 1500.00, 397.10, 0.85);

COMMIT;