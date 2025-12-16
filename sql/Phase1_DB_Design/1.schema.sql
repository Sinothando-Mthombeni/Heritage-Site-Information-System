-- =========================================
-- Heritage Sites Database Schema
-- PostgreSQL | Phase 2
-- =========================================

DROP TABLE IF EXISTS review CASCADE;
DROP TABLE IF EXISTS booking CASCADE;
DROP TABLE IF EXISTS visitor CASCADE;
DROP TABLE IF EXISTS heritage_site CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS province CASCADE;

CREATE TABLE province (
    province_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE category (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE heritage_site (
    site_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    province_id INT NOT NULL,
    category_id INT NOT NULL,
    established_year INT,
    entry_fee NUMERIC(8,2),
    FOREIGN KEY (province_id) REFERENCES province(province_id),
    FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE visitor (
    visitor_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    registration_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE booking (
    booking_id SERIAL PRIMARY KEY,
    visitor_id INT NOT NULL,
    site_id INT NOT NULL,
    booking_date DATE NOT NULL,
    visit_date DATE NOT NULL,
    number_of_tickets INT CHECK (number_of_tickets > 0),
    FOREIGN KEY (visitor_id) REFERENCES visitor(visitor_id),
    FOREIGN KEY (site_id) REFERENCES heritage_site(site_id)
);

CREATE TABLE review (
    review_id SERIAL PRIMARY KEY,
    visitor_id INT NOT NULL,
    site_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    review_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (visitor_id) REFERENCES visitor(visitor_id),
    FOREIGN KEY (site_id) REFERENCES heritage_site(site_id),
    UNIQUE (visitor_id, site_id)
);
