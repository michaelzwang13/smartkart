-- Select the database
USE hacknyu25;

-- Create the user table (renamed to user_account)
CREATE TABLE user_account (
    user_ID VARCHAR(50),
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    PRIMARY KEY (user_ID)
);

-- Create the cart table
CREATE TABLE cart (
    cart_ID INT AUTO_INCREMENT,
    user_ID VARCHAR(50),
    store_name VARCHAR(25) NOT NULL,
    status ENUM('active', 'purchased') NOT NULL,
    PRIMARY KEY (cart_ID),                         
    FOREIGN KEY (user_ID) REFERENCES user_account(user_ID)
);

-- Create the item table
CREATE TABLE item (
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
    FOREIGN KEY (cart_ID) REFERENCES cart(cart_ID),
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

CREATE TABLE budgets (
    user_ID VARCHAR(50),
    month INT,
    year INT,
    budget DECIMAL(10,2),
    PRIMARY KEY (user_ID, month, year)
);

CREATE TABLE shopping_list (
    list_id INT AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    status ENUM('pending', 'purchased') NOT NULL DEFAULT 'pending',
    PRIMARY KEY (list_id),
    FOREIGN KEY (user_id) REFERENCES user_account(user_ID)
);
