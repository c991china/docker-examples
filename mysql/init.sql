-- Seed schema for the mysql example. Runs once, on first container start,
-- because MySQL only executes /docker-entrypoint-initdb.d/* when the data
-- directory is empty.
--
--   docker run --rm -d --name mysql-demo \
--     -e MYSQL_ROOT_PASSWORD=devroot -e MYSQL_DATABASE=shop \
--     -v "$PWD/mysql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro" \
--     -p 3306:3306 mysql:8.0

SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE IF NOT EXISTS customers (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email       VARCHAR(255) NOT NULL,
    full_name   VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_customers_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id  BIGINT UNSIGNED NOT NULL,
    status       ENUM('pending','paid','shipped','cancelled') NOT NULL DEFAULT 'pending',
    total_cents  INT UNSIGNED NOT NULL DEFAULT 0,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_orders_customer (customer_id),
    KEY idx_orders_status (status),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO customers (email, full_name) VALUES
    ('ada@example.com',   'Ada Lovelace'),
    ('grace@example.com', 'Grace Hopper'),
    ('linus@example.com', 'Linus Torvalds')
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

INSERT INTO orders (customer_id, status, total_cents) VALUES
    (1, 'paid',    2599),
    (1, 'shipped', 1099),
    (2, 'pending', 4999)
ON DUPLICATE KEY UPDATE status = VALUES(status);

-- Handy sanity check when you exec into the container:
--   SELECT c.full_name, COUNT(o.id) AS orders, SUM(o.total_cents) AS cents
--   FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
--   GROUP BY c.id;
