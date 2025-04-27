-- ====== DROP TABLES IF EXISTS ======
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS rentals CASCADE;
DROP TABLE IF EXISTS cars CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- ====== CREATE TABLES ======

-- Rollen
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) UNIQUE NOT NULL
);

-- Gebruikers
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- Auto's
CREATE TABLE cars (
    car_id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    daily_price NUMERIC(10,2) NOT NULL,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('available', 'rented', 'maintenance')),
    user_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_car_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);


-- Verhuringen
CREATE TABLE rentals (
    rental_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    car_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_price NUMERIC(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('ongoing', 'completed', 'cancelled')),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_car FOREIGN KEY (car_id) REFERENCES cars(car_id)
);

-- Betalingen
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    rental_id INT NOT NULL,
    payment_date DATE NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('credit_card', 'paypal', 'bank_transfer')),
    CONSTRAINT fk_rental FOREIGN KEY (rental_id) REFERENCES rentals(rental_id)
);

-- ====== INSERT INITIËLE ROLLEN ======
INSERT INTO roles (role_name) VALUES
('admin'),
('customer');

-- ====== INSERT INITIËLE AUTO'S ======
INSERT INTO cars (brand, model, year, daily_price, license_plate, status) VALUES
('Lamborghini', 'Aventador', 2022, 1200.00, 'LMB-001', 'available'),
('Ferrari', '488 GTB', 2021, 1000.00, 'FER-002', 'available'),
('Maserati', 'Levante', 2020, 800.00, 'MAS-003', 'available'),
('Porsche', '911 GT3', 2023, 1100.00, 'POR-004', 'available'),
('Rolls Royce', 'Ghost', 2022, 1500.00, 'RR-005', 'available');

-- ====== TRIGGERS ======

-- Auto status op 'rented' zetten na verhuur
CREATE OR REPLACE FUNCTION update_car_status_on_rental()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cars
    SET status = 'rented'
    WHERE car_id = NEW.car_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_car_status
AFTER INSERT ON rentals
FOR EACH ROW
EXECUTE FUNCTION update_car_status_on_rental();

-- Auto terug op 'available' zetten na huur beëindiging
CREATE OR REPLACE FUNCTION set_car_available_on_rental_end()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        UPDATE cars
        SET status = 'available'
        WHERE car_id = NEW.car_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_car_available
AFTER UPDATE ON rentals
FOR EACH ROW
WHEN (OLD.status != 'completed' AND NEW.status = 'completed')
EXECUTE FUNCTION set_car_available_on_rental_end();

-- ====== STORED PROCEDURE ======

-- Verhuur en betaling tegelijk aanmaken
CREATE OR REPLACE PROCEDURE create_rental_and_payment(
    p_user_id UUID,
    p_car_id INT,
    p_start_date DATE,
    p_end_date DATE,
    p_total_price NUMERIC,
    p_amount NUMERIC,
    p_payment_method VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    rental_id_created INT;
BEGIN
    INSERT INTO rentals (user_id, car_id, start_date, end_date, total_price, status)
    VALUES (p_user_id, p_car_id, p_start_date, p_end_date, p_total_price, 'ongoing')
    RETURNING rental_id INTO rental_id_created;

    INSERT INTO payments (rental_id, payment_date, amount, payment_method)
    VALUES (rental_id_created, CURRENT_DATE, p_amount, p_payment_method);
END;
$$;

-- ====== ADMIN DASHBOARD VIEW ======

CREATE OR REPLACE VIEW admin_dashboard AS
SELECT
    r.rental_id,
    u.name AS klant_naam,
    u.email AS klant_email,
    c.brand || ' ' || c.model AS auto,
    r.start_date,
    r.end_date,
    r.status AS rental_status,
    p.amount AS betaalde_bedrag,
    p.payment_method,
    p.payment_date,
    c.status AS auto_status
FROM rentals r
JOIN users u ON r.user_id = u.user_id
JOIN cars c ON r.car_id = c.car_id
LEFT JOIN payments p ON r.rental_id = p.rental_id
ORDER BY r.start_date DESC;

-- ====== EXTENSIE ======

-- Nodig voor UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ====== SECURITY: ROLLEN EN RECHTEN ======

CREATE ROLE rental_admin LOGIN PASSWORD 'AdminPassword123';
CREATE ROLE rental_user LOGIN PASSWORD 'UserPassword123';

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rental_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rental_admin;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rental_user;
