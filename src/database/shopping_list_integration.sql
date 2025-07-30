    -- Additional schema modifications for shopping list integration with shopping trips
    USE hacknyu25;

    -- Add a shopping_list_id field to shopping_cart table to link trips with lists
    ALTER TABLE shopping_cart 
    ADD COLUMN shopping_list_id INT NULL,
    ADD FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(list_id);

    -- Create a table to track which list items have been added to cart during shopping
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