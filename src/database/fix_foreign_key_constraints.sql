-- Fix foreign key constraints for shopping list integration
-- This script updates existing foreign key constraints to include CASCADE options
USE hacknyu25;

-- Drop existing foreign key constraints if they exist
SET FOREIGN_KEY_CHECKS = 0;

-- Drop the table and recreate it with proper CASCADE constraints
DROP TABLE IF EXISTS shopping_list_cart_mapping;

-- Recreate the table with proper CASCADE constraints
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

SET FOREIGN_KEY_CHECKS = 1;

-- Note: This will delete any existing mapping data
-- Run this only if you're okay with losing current shopping list mappings
-- or if you're setting up a fresh database