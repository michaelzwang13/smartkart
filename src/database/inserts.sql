REATE TABLE user(
    user_ID VARCHAR(50),
    email VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    date_registered DATETIME NOT NULL,
    PRIMARY KEY(user_ID)
)

CREATE TABLE cart(
    cart_ID INT,
    user_ID VARCHAR(50) NOT NULL,
    date_brought DATETIME NOT NULL,
    PRIMARY KEY(cart_ID)
    FOREIGN KEY(user_ID) AND REFERENCES user(user_ID)
)

CREATE TABLE item(
    item_ID INT,
    cart_ID INT NOT NULL,
    quantity INT NOT NULL,
    PRIMARY KEY(item_ID)
    FOREIGN KEY(cart_ID) AND REFERENCES cart(cart_ID)
)

-- Achievement functionality

CREATE TABLE achievements(
    achievement_ID INT,
    name VARCHAR(100) NOT NULL,
    points INT NOT NULL,
    description VARCHAR(500) NOT NULL,
)

CREATE TABLE user_achievements(
    user_ID INT,
    achievement_ID INT NOT NULL,
    date_earned DATETIME NOT NULL,
    FOREIGN KEY(user_ID) AND REFERENCES user(user_ID)
    FOREIGN KEY(achievement_ID) AND REFERENCES achievement(achievement_ID)
)