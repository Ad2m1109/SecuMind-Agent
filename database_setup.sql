-- Database: memoire_project
-- Complete database setup for Sentinel AI system

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS memoire_project;
USE memoire_project;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts table (replaces alerts.csv)
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attack_type VARCHAR(100) NOT NULL,
    failed_attempts INT DEFAULT 0,
    severity_score FLOAT DEFAULT 0.0,
    ip_reputation FLOAT DEFAULT 0.0,
    previous_incidents INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processed alerts history table (replaces processed_alerts.csv)
CREATE TABLE IF NOT EXISTS processed_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attack_type VARCHAR(100),
    failed_attempts INT,
    severity_score FLOAT,
    ip_reputation FLOAT,
    previous_incidents INT,
    source_ip VARCHAR(45),
    decision VARCHAR(50),
    confidence FLOAT,
    action VARCHAR(50),
    explanation TEXT,
    analyst_email VARCHAR(255),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_alerts_attack_type ON alerts(attack_type);
CREATE INDEX idx_processed_alerts_decision ON processed_alerts(decision);
CREATE INDEX idx_processed_alerts_processed_at ON processed_alerts(processed_at);

-- Optional: Insert a default admin user (password: admin123 hashed with bcrypt)
INSERT IGNORE INTO users (email, password) VALUES
('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uUkK6kzcQ8mO');

-- Optional: Insert sample alerts (you can import from CSV later)
INSERT IGNORE INTO alerts (attack_type, failed_attempts, severity_score, ip_reputation, previous_incidents) VALUES
('brute_force', 15, 0.8, 0.9, 2),
('malware', 0, 0.6, 0.3, 1),
('scan', 5, 0.2, 0.1, 0),
('ddos', 100, 0.95, 0.95, 5);

-- Note: The password hash above is for 'admin123'
-- To generate your own: python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('yourpassword'))"