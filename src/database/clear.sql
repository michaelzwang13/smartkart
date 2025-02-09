-- clear.sql

-- Make sure you're in the right database (optional, if you're certain)
USE hacknyu25;

-- Disable foreign key checks to avoid errors when dropping tables with dependencies
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS user_achievements;
DROP TABLE IF EXISTS achievements;
DROP TABLE IF EXISTS item;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS user_account;
DROP TABLE IF EXISTS budgets;
DROP TABLE IF EXISTS shopping_list;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;
