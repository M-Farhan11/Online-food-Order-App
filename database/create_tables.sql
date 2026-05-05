CREATE DATABASE IF NOT EXISTS online_food_app;
USE online_food_app;

CREATE TABLE IF NOT EXISTS users (
    user_id  INT          AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    phone    VARCHAR(15)  UNIQUE NOT NULL,
    password VARCHAR(60)  NOT NULL
);

CREATE TABLE IF NOT EXISTS menu_items (
    item_id      INT            AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100)   NOT NULL,
    category     VARCHAR(50)    NOT NULL,
    price        DECIMAL(10,2)  NOT NULL,
    is_available TINYINT(1)     NOT NULL DEFAULT 1,
    image_path   VARCHAR(255)   DEFAULT NULL   -- relative path e.g. images/burger.jpg
);

CREATE TABLE IF NOT EXISTS orders (
    order_id       INT            AUTO_INCREMENT PRIMARY KEY,
    user_id        INT            NOT NULL,
    total_amount   DECIMAL(10,2)  NOT NULL,
    status         VARCHAR(50)    NOT NULL DEFAULT 'Placed',
    payment_method VARCHAR(50)    NOT NULL DEFAULT 'Cash on Delivery',
    created_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
    id            INT            AUTO_INCREMENT PRIMARY KEY,
    order_id      INT            NOT NULL,
    item_id       INT            NOT NULL,
    item_name     VARCHAR(100)   NOT NULL,
    item_category VARCHAR(50)    NOT NULL,
    item_price    DECIMAL(10,2)  NOT NULL,
    quantity      INT            NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id      INT            AUTO_INCREMENT PRIMARY KEY,
    order_id        INT            NOT NULL UNIQUE,
    method          VARCHAR(50)    NOT NULL,
    amount          DECIMAL(10,2)  NOT NULL,
    transaction_ref VARCHAR(100)   DEFAULT NULL,
    paid_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

INSERT IGNORE INTO menu_items (name, category, price) VALUES
    ('Classic Beef Burger',   'Burgers', 450.00),
    ('Crispy Chicken Burger', 'Burgers', 400.00),
    ('Double Smash Burger',   'Burgers', 650.00),
    ('Margherita Pizza',      'Pizzas',  700.00),
    ('BBQ Chicken Pizza',     'Pizzas',  850.00),
    ('Veggie Supreme Pizza',  'Pizzas',  750.00),
    ('Fresh Lemonade',        'Drinks',  150.00),
    ('Mango Shake',           'Drinks',  200.00),
    ('Cola Can',              'Drinks',   80.00),
    ('French Fries (Large)',  'Sides',   220.00),
    ('Onion Rings',           'Sides',   180.00);