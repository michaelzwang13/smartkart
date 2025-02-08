-- Select the database
USE hacknyu25;

-- Create the user table (renamed to user_account)
CREATE TABLE user_account (
    user_ID VARCHAR(50),
    email VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    PRIMARY KEY (user_ID)
);

-- Create the cart table
CREATE TABLE cart (
    cart_ID INT AUTO_INCREMENT,
    user_ID VARCHAR(50) NOT NULL,
    date_brought DATETIME NOT NULL,
    PRIMARY KEY (cart_ID),
    FOREIGN KEY (user_ID) REFERENCES user_account(user_ID)
);

-- Create the item table
CREATE TABLE item (
    item_ID INT AUTO_INCREMENT,
    cart_ID INT NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY (item_ID),
    FOREIGN KEY (cart_ID) REFERENCES cart(cart_ID)
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
    user_ID VARCHAR(50) NOT NULL,
    achievement_ID INT NOT NULL,
    date_earned DATETIME NOT NULL,
    PRIMARY KEY (user_ID, achievement_ID),
    FOREIGN KEY (user_ID) REFERENCES user_account(user_ID),
    FOREIGN KEY (achievement_ID) REFERENCES achievements(achievement_ID)
);
