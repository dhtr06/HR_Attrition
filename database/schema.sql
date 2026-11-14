CREATE DATABASE IF NOT EXISTS hr_attrition CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hr_attrition;
CREATE TABLE IF NOT EXISTS employees (
 id INT AUTO_INCREMENT PRIMARY KEY,
 employee_code VARCHAR(30) NOT NULL UNIQUE,
 full_name VARCHAR(150) NOT NULL,
 age INT, department VARCHAR(100), job_role VARCHAR(100),
 monthly_income DECIMAL(12,2), years_at_company DECIMAL(5,2),
 overtime VARCHAR(10), job_satisfaction INT, work_life_balance INT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS prediction_history (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 employee_id INT NULL,
 probability DECIMAL(7,6) NOT NULL,
 risk_level VARCHAR(20) NOT NULL,
 model_name VARCHAR(100),
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
);
