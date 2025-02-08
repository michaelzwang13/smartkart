-- inserts.sql
-- Make sure you're in the correct database
USE hacknyu25;

-- 1. Insert USERS (user_account)
INSERT INTO user_account (user_ID, email, password)
VALUES
('john_doe', 'john@example.com', '202cb962ac59075b964b07152d234b70'),
('jane_smith', 'jane@example.com', '202cb962ac59075b964b07152d234b70');

-- 2. Insert CARTS
-- cart_ID is AUTO_INCREMENT, so we omit it in the insert.
-- Once inserted, MySQL will generate cart_ID=1,2,3,... in sequence.
INSERT INTO cart (cart_ID, user_ID, store_name, status)
VALUES
(1, 'john_doe', 'Walmart', 'active'),
(2, 'john_doe', 'Costco', 'purchased'),
(3, 'jane_smith', 'Target', 'purchased');

-- After these inserts:
--   cart_ID=1 -> (user_ID='john_doe', store_name='Walmart',   status='active')
--   cart_ID=2 -> (user_ID='john_doe', store_name='Costco',    status='purchased')
--   cart_ID=3 -> (user_ID='jane_smith', store_name='Target',  status='purchased')

-- 3. Insert ITEMS
-- item_ID is AUTO_INCREMENT. We only specify cart_ID and other fields.
-- Adjust references to the correct cart_IDs from the previous step.
INSERT INTO item (item_ID, cart_ID, user_ID, quantity, price, item_name, upc, item_lifetime)
VALUES
(1, 1, 'john_doe', 1, 3.99, 'Bread', 12345, 7),      -- Goes in cart_ID=1
(2, 1, 'john_doe', 2, 5.99, 'Milk', 67890, 5),
(3, 3, 'jane_smith', 20, 250.00, 'Laptop', 11111, 365),   -- Goes in cart_ID=2
(4, 3, 'jane_smith', 3, 4.99, 'Juice', 22222, 10),    -- Goes in cart_ID=3
(5, 3, 'jane_smith', 3, 1.99, 'Apples', 33333, 3);

-- 4. Insert ACHIEVEMENTS
-- achievement_ID is AUTO_INCREMENT.
INSERT INTO achievements (achievement_ID, name, points, description)
VALUES
(1, 'First Purchase', 10, 'Successfully made the first purchase'),
(2, 'Impulse-Free Week', 25, 'No impulse items for an entire week'),
(3, 'Budget Master', 50, 'Stayed under monthly budget for 3 consecutive months');

-- After insertion:
--   achievement_ID=1 -> First Purchase
--   achievement_ID=2 -> Impulse-Free Week
--   achievement_ID=3 -> Budget Master

-- 5. Insert USER_ACHIEVEMENTS
-- The PK is (user_ID, achievement_ID).
-- We assume the auto-increment IDs for achievements as above (1,2,3).
INSERT INTO user_achievements (user_ID, achievement_ID, date_earned)
VALUES
('john_doe', 1, '2025-03-01 12:00:00'),  -- John earned "First Purchase"
('john_doe', 2, '2025-03-08 09:30:00'),  -- John earned "Impulse-Free Week"
('jane_smith', 1, '2025-03-05 10:15:00');-- Jane earned "First Purchase"

-- 6. Insert BUDGETS
-- The PK is (user_ID, month, year).
INSERT INTO budgets (user_ID, month, year, budget)
VALUES
('john_doe', 3, 2025, 150.00),   -- March 2025 budget
('jane_smith', 3, 2025, 200.00); -- March 2025 budget

INSERT INTO shopping_list (user_id, item_name, quantity, status)
VALUES
('john_doe', 'Toilet Paper', 2, 'pending'),
('john_doe', 'Dish Soap', 1, 'pending'),
('john_doe', 'Bananas', 6, 'purchased'),
('jane_smith', 'Eggs', 12, 'pending'),
('jane_smith', 'Milk', 1, 'purchased');
