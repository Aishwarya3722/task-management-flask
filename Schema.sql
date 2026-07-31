-- ============================================================
-- Task Management System — Database Schema (MySQL)
-- ============================================================
-- Run this once to create the database and tables:
--   mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS task_management;
USE task_management;

-- ------------------------------------------------------------
-- Table 1: admin_login  (admin/login credentials)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_login (
    admin_id      INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed admin user -> username: admin | password: admin123
-- (change this password after first login in a real deployment)
INSERT INTO admin_login (username, password_hash)
VALUES ('admin', 'scrypt:32768:8:1$L6k1IpgNVhAnnEXY$de0160ab591e2df30e85ba103746b55653b95c877346d72a214fcdb243afe9d32a8e26eedd7abc6debc41f198c204392f178a6558e83f0adc0bc903d00435330')
ON DUPLICATE KEY UPDATE username = username;

-- ------------------------------------------------------------
-- Table 2: employees  (referenced by task_management via FK)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    employee_id   INT AUTO_INCREMENT PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL
);

-- A few sample employees so the task form's dropdown isn't empty
INSERT INTO employees (employee_name) VALUES
    ('Aditi Sharma'),
    ('Rohan Verma'),
    ('Priya Nair')
ON DUPLICATE KEY UPDATE employee_name = employee_name;

-- ------------------------------------------------------------
-- Table 3: task_management  (matches your sketch)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_management (
    task_id     INT AUTO_INCREMENT PRIMARY KEY,   -- pk, auto_increment
    employee_id INT NOT NULL,                     -- FK -> employees
    task_title  VARCHAR(255) NOT NULL,
    completed   ENUM('true','false') NOT NULL DEFAULT 'false',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_task_employee
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        ON DELETE CASCADE
);
