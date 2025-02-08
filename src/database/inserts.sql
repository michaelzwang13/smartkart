CREATE TABLE airline(
    name VARCHAR(30),
    PRIMARY KEY(name)
);
   
CREATE TABLE airplane(
    airline_name VARCHAR(50),
    airplane_ID INT,
    num_seats INT NOT NULL,
    manufacturing_company VARCHAR(50) NOT NULL,
    model_num VARCHAR(15) NOT NULL,
    manufacturing_date DATE NOT NULL,
    age INT NOT NULL,
    PRIMARY KEY(airline_name, airplane_ID),
    FOREIGN KEY(airline_name) REFERENCES airline(name)
);

CREATE TABLE airport(
    code VARCHAR(20),
    name VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL,
    num_terminals INT NOT NULL,
    airport_type VARCHAR(30) NOT NULL,
	PRIMARY KEY (code)
);

CREATE TABLE flight(
    airline_name VARCHAR(50),
    flight_number VARCHAR(50),
    departure_time TIME,
    departure_date DATE,
    arrival_date DATE NOT NULL,
    arrival_time TIME NOT NULL,
    base_price FLOAT NOT NULL,
    flight_status VARCHAR(20) NOT NULL,
    departure_airport_code VARCHAR(20) NOT NULL,
    arrival_airport_code VARCHAR(20) NOT NULL,
    airplane_id INT,
    PRIMARY KEY(airline_name,flight_number,departure_time,departure_date),
    FOREIGN KEY(airline_name,airplane_id) REFERENCES airplane(airline_name,airplane_ID),
    FOREIGN KEY(departure_airport_code) REFERENCES airport(code),
    FOREIGN KEY(arrival_airport_code) REFERENCES airport(code)
);

CREATE TABLE ticket(
    ID INT,
    ticket_price FLOAT NOT NULL,
    airline_name VARCHAR(50),
    flight_number VARCHAR(50),
    departure_time TIME,
    departure_date DATE,
    PRIMARY KEY(ID),
    FOREIGN KEY(airline_name,flight_number,departure_time,departure_date) REFERENCES flight(airline_name,flight_number,departure_time,departure_date)
);

CREATE TABLE airline_staff(
    username VARCHAR(50),
    airline_name VARCHAR(50),
    password VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    PRIMARY KEY (username),
    FOREIGN KEY (airline_name) REFERENCES airline(name)
);
 
CREATE TABLE customer(
    email_address VARCHAR(50),
    password VARCHAR(50) NOT NULL,
    first_name VARCHAR(50)NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    building_name VARCHAR(50) NOT NULL,
    street_name VARCHAR(50) NOT NULL,
    apt_num VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zipcode INT NOT NULL, 
    date_of_birth DATE NOT NULL,
    passport_number VARCHAR(50) NOT NULL,
    passport_expiration DATE NOT NULL,
    passport_country VARCHAR(50) NOT NULL,
    PRIMARY KEY (email_address)
);

CREATE TABLE customer_phone_number(
    email_address VARCHAR(50),
    phone_number VARCHAR(50),
    PRIMARY KEY(email_address,phone_number),
    FOREIGN KEY(email_address) REFERENCES customer(email_address)
);

CREATE TABLE airline_staff_phone_number(
    username VARCHAR(50),
    phone_number VARCHAR(50),
    PRIMARY KEY(username,phone_number),
    FOREIGN KEY(username) REFERENCES airline_staff(username)
);

CREATE TABLE airline_staff_email(
    username VARCHAR(50),
    email_address VARCHAR(50),
    PRIMARY KEY(username,email_address),
    FOREIGN KEY(username) REFERENCES airline_staff(username)
);

CREATE TABLE maintenance_procedure(
    airline_name VARCHAR(50),
    airplane_ID INT,
    maintenance_start_time TIME NOT NULL,
    maintenance_start_date DATE NOT NULL,
    maintenance_end_time TIME NOT NULL,
    maintenance_end_date DATE NOT NULL,
    PRIMARY KEY (airline_name,airplane_ID),
    FOREIGN KEY (airline_name,airplane_ID) REFERENCES airplane(airline_name,airplane_ID)
);

CREATE TABLE rate(
    email_address VARCHAR(50),
    airline_name VARCHAR(50),
    flight_number VARCHAR(50),
    departure_time TIME,
    departure_date DATE,
    comments VARCHAR(100) NOT NULL,
    rating INT NOT NULL,
    PRIMARY KEY(email_address,airline_name,flight_number,departure_time,departure_date),
    FOREIGN KEY (email_address) REFERENCES customer(email_address),
    FOREIGN KEY (airline_name,flight_number,departure_time,departure_date) REFERENCES flight(airline_name,flight_number,departure_time,departure_date)
);

CREATE TABLE purchase(
    email_address VARCHAR(50),
    ID INT,
    ticket_user_first_name VARCHAR(50) NOT NULL,
    ticket_user_last_name VARCHAR(50) NOT NULL,
    ticket_user_date_of_birth DATE NOT NULL,
    purchase_date DATE NOT NULL,
    purchase_time TIME NOT NULL,
    card_type VARCHAR(50) NOT NULL,
    card_number DECIMAL(20,0) NOT NULL,
    card_name VARCHAR(50) NOT NULL,
    expiration_date DATE NOT NULL,
    PRIMARY KEY(email_address,ID),
    FOREIGN KEY(email_address) REFERENCES customer(email_address),
    FOREIGN KEY(ID) REFERENCES ticket(ID)
);


INSERT INTO airline (name) VALUES 
('Delta Air Lines'),
('American Airlines'),
('United Airlines'),
('Southwest Airlines'),
('Alaska Airlines'),
('JetBlue Airways');


INSERT INTO airport (code, name, city, country, num_terminals, airport_type) VALUES
('JFK', 'John F. Kennedy International Airport', 'New York', 'United States', 6, 'Both'),
('LAX', 'Los Angeles International Airport', 'Los Angeles', 'United States', 9, 'Both'),
('PVG', 'Shanghai Pudong International Airport', 'Shanghai', 'China', 2, 'Both');


INSERT INTO customer (email_address, password, first_name, last_name, building_name, street_name, apt_num, city, state, zipcode, date_of_birth, passport_number, passport_expiration, passport_country) VALUES
('john.doe@gmail.com', 'password123', 'John', 'Doe', 'Greenwood Apartments', 'Main Street', '101', 'New York', 'NY', 10001, '1985-03-15', 'P12345678', '2030-05-15', 'United States'),
('bob.johnson@aol.com', 'securepass456', 'Bob', 'Johnson', 'Riverfront Condos', 'Broadway', '5A', 'Los Angeles', 'CA', 90012, '1990-07-22', 'P87654321', '2029-08-10', 'United States'),
('emma.green@icloud.com', 'emma2023!', 'Emma', 'Green', 'Sunset Towers', 'Market Street', '12B', 'San Francisco', 'CA', 94103, '1988-11-10', 'C65432189', '2028-11-20', 'Canada'),
('kevin.li@protonmail.com', 'k3vinli$', 'Kevin', 'Li', 'Highrise Plaza', 'Elm Street', '22C', 'Seattle', 'WA', 98101, '1993-12-05', 'D28374659', '2032-04-25', 'China');


INSERT INTO airplane (airline_name, airplane_ID, num_seats, manufacturing_company, model_num, manufacturing_date, age) VALUES
('Delta Air Lines', 1012, 180, 'Boeing', '737', '2015-06-15', 9),
('Delta Air Lines', 1025, 200, 'Airbus', 'A320', '2018-04-20', 6),
('Delta Air Lines', 1043, 250, 'Boeing', '757', '2012-07-10', 12),
('American Airlines', 2018, 250, 'Boeing', '757', '2014-08-12', 10),
('American Airlines', 2055, 300, 'Airbus', 'A321', '2019-09-15', 5),
('United Airlines', 3019, 280, 'Boeing', '777', '2012-03-10', 12),
('United Airlines', 3041, 320, 'Airbus', 'A330', '2016-07-25', 8),
('Southwest Airlines', 4012, 175, 'Boeing', '737', '2013-11-20', 11),
('Southwest Airlines', 4038, 175, 'Boeing', '737', '2017-01-15', 7),
('Southwest Airlines', 4067, 189, 'Boeing', '737 MAX 8', '2019-09-10', 5),
('Alaska Airlines', 5021, 160, 'Airbus', 'A320', '2016-06-18', 8),
('Alaska Airlines', 5074, 190, 'Boeing', '737', '2018-10-10', 6),
('Alaska Airlines', 5089, 200, 'Boeing', '737 MAX 9', '2020-01-15', 4),
('JetBlue Airways', 6014, 150, 'Embraer', 'E190', '2014-04-12', 10),
('JetBlue Airways', 6043, 200, 'Airbus', 'A321', '2020-03-20', 4);


INSERT INTO airline_staff (username, airline_name, password, first_name, last_name, date_of_birth) VALUES
('john_doe', 'Delta Air Lines', 'delta123', 'John', 'Doe', '1985-03-15'),
('jane_smith', 'Delta Air Lines', 'delta456', 'Jane', 'Smith', '1990-07-22'),
('michael_brown', 'American Airlines', 'aa123', 'Michael', 'Brown', '1988-04-15'),
('emma_green', 'American Airlines', 'aa456', 'Emma', 'Green', '1992-11-30'),
('logan_davis', 'United Airlines', 'united123', 'Logan', 'Davis', '1987-05-10'),
('alice_wang', 'United Airlines', 'united456', 'Alice', 'Wang', '1995-06-25'),
('kevin_li', 'Southwest Airlines', 'sw123', 'Kevin', 'Li', '1989-10-12'),
('sophia_martinez', 'Southwest Airlines', 'sw456', 'Sophia', 'Martinez', '1993-03-18'),
('lucas_martin', 'Alaska Airlines', 'alaska123', 'Lucas', 'Martin', '1980-12-01'),
('mia_robinson', 'Alaska Airlines', 'alaska456', 'Mia', 'Robinson', '1990-08-08'),
('ethan_clark', 'JetBlue Airways', 'jetblue123', 'Ethan', 'Clark', '1985-01-20'),
('amelia_jones', 'JetBlue Airways', 'jetblue456', 'Amelia', 'Jones', '1992-04-05');


INSERT INTO flight (airline_name, flight_number, departure_time, departure_date, arrival_date, arrival_time, base_price, flight_status, departure_airport_code, arrival_airport_code, airplane_id) VALUES
('Delta Air Lines', 'DL4521A', '08:00:00', '2024-11-10', '2024-11-10', '11:30:00', 251.46, 'On-Time', 'JFK', 'LAX', 1012),
('Delta Air Lines', 'DL3892B', '15:00:00', '2024-11-10', '2024-11-10', '18:00:00', 324.54, 'Delayed', 'LAX', 'PVG', 1025),
('American Airlines', 'AA9841A', '06:30:00', '2024-11-10', '2024-11-10', '10:00:00', 290.21, 'On-Time', 'LAX', 'JFK', 2018),
('American Airlines', 'AA7123B', '16:00:00', '2024-11-10', '2024-11-10', '20:00:00', 310.65, 'Delayed', 'PVG', 'JFK', 2055),
('United Airlines', 'UA5132A', '09:00:00', '2024-11-10', '2024-11-10', '12:00:00', 310.52, 'Canceled', 'LAX', 'JFK', 3019),
('United Airlines', 'UA6829B', '13:30:00', '2024-11-10', '2024-11-10', '16:30:00', 280.12, 'Delayed', 'JFK', 'PVG', 3041),
('Southwest Airlines', 'SW2394C', '12:00:00', '2024-11-11', '2024-11-11', '14:00:00', 180.16, 'On-Time', 'PVG', 'LAX', 4067),
('Southwest Airlines', 'SW7418D', '08:30:00', '2024-11-12', '2024-11-12', '11:00:00', 210.74, 'Delayed', 'LAX', 'JFK', 4012),
('Alaska Airlines', 'AS7324A', '10:30:00', '2024-11-10', '2024-11-10', '13:45:00', 270.15, 'On-Time', 'JFK', 'LAX', 5021),
('JetBlue Airways', 'JB6078C', '10:30:00', '2024-11-11', '2024-11-11', '13:15:00', 230.64, 'Canceled', 'JFK', 'PVG', 6014);

INSERT INTO ticket (ID, ticket_price, airline_name, flight_number, departure_time, departure_date) VALUES
(9845, 251.46, 'Delta Air Lines', 'DL4521A', '08:00:00', '2024-11-10'),
(5382, 251.46, 'Delta Air Lines', 'DL4521A', '08:00:00', '2024-11-10'),
(1276, 324.54, 'Delta Air Lines', 'DL3892B', '15:00:00', '2024-11-10'),
(1139, 290.21, 'American Airlines', 'AA9841A', '06:30:00', '2024-11-10'),
(8421, 310.65 , 'American Airlines', 'AA7123B', '16:00:00', '2024-11-10'),
(6187, 310.52, 'United Airlines', 'UA5132A', '09:00:00', '2024-11-10'),
(8435, 280.12, 'United Airlines', 'UA6829B', '13:30:00', '2024-11-10'),
(5037, 180.16, 'Southwest Airlines', 'SW2394C', '12:00:00', '2024-11-11'),
(9742, 210.74, 'Southwest Airlines', 'SW7418D', '08:30:00', '2024-11-12'),
(5918, 270.15, 'Alaska Airlines', 'AS7324A', '10:30:00', '2024-11-10'),
(2389, 270.15, 'Alaska Airlines', 'AS7324A', '10:30:00', '2024-11-10'),
(9042, 230.64, 'JetBlue Airways', 'JB6078C', '10:30:00', '2024-11-11');


INSERT INTO purchase (email_address, ID, ticket_user_first_name, ticket_user_last_name, ticket_user_date_of_birth, purchase_date, purchase_time, card_type, card_number, card_name, expiration_date) VALUES
('john.doe@gmail.com', 9845, 'John', 'Doe', '1985-03-15', '2024-11-01', '12:34:56', 'Visa', 4111111111111111, 'John Doe', '2025-05-15'),
('john.doe@gmail.com', 5382, 'Anna', 'Doe', '2005-01-01', '2024-11-01', '12:35:40', 'Visa', 4111111111111111, 'John Doe', '2025-05-15'),
('john.doe@gmail.com', 1276, 'John', 'Doe', '1985-03-15', '2024-11-02', '13:15:22', 'MasterCard', 5123456789012345, 'John Doe', '2026-08-10'),
('bob.johnson@aol.com', 1139, 'Bob', 'Johnson', '1980-05-05', '2024-11-06', '12:34:12', 'Discover', 6011222233334444, 'Bob Johnson', '2032-09-15'),
('bob.johnson@aol.com', 8421, 'Donald', 'Johnson', '1987-11-01', '2024-11-07', '16:30:12', 'Visa', 4111111113333333, 'Bob Johnson', '2029-07-11'),
('bob.johnson@aol.com', 6187, 'Bob', 'Johnson', '1980-05-05', '2024-11-08', '12:45:30', 'American Express', 371449635446631, 'Bob Johnson', '2031-06-30'),
('bob.johnson@aol.com', 8435, 'Vincent', 'Johnson', '2006-08-19', '2024-11-08', '12:46:10', 'American Express', 371449635446631, 'Bob Johnson', '2031-06-30'),
('emma.green@icloud.com', 5037, 'Emma', 'Green', '1995-01-22', '2024-11-09', '08:30:50', 'Discover', 6011000990139424, 'Emma Green', '2030-02-20'),
('emma.green@icloud.com', 9742, 'Lebron', 'Green', '1997-06-05', '2024-11-09', '08:32:15', 'Discover', 6011000990139424, 'Emma Green', '2030-02-20'),
('kevin.li@protonmail.com', 5918, 'Kevin', 'Li', '1993-12-05', '2024-11-10', '09:15:25', 'Visa', 4111111112223333, 'Kevin Li', '2029-06-30'),
('kevin.li@protonmail.com', 2389, 'Rammon', 'Li', '2011-09-18', '2024-11-10', '09:16:45', 'Visa', 4111111112223333, 'Kevin Li', '2029-06-30'),
('kevin.li@protonmail.com', 9042, 'Kevin', 'Li', '1993-12-05', '2024-11-10', '10:05:22', 'MasterCard', 5123456789012345, 'Kevin Li', '2032-04-25');
