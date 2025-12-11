-- ===========================================
-- CREATE DATABASE
-- ===========================================
CREATE DATABASE IF NOT EXISTS python;
USE python;

-- ===========================================
-- 1. USER TABLE
-- ===========================================
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(250) UNIQUE,
    passwords VARCHAR(255),
    avatar VARCHAR(255) DEFAULT 'default-avatar.png',
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_country VARCHAR(10),
    phone_number VARCHAR(40),
    gender VARCHAR(20),
    about TEXT,
    is_admin TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- 2. SAVED TRIPS
-- ===========================================
CREATE TABLE saved_trips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    sub VARCHAR(255),
    img VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- ===========================================
-- 3. ADMIN LOGS
-- ===========================================
CREATE TABLE admin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT,
    action VARCHAR(255),
    meta TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- 4. USER ANALYTICS
-- ===========================================
CREATE TABLE user_analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    ip VARCHAR(50),
    city VARCHAR(100),
    country VARCHAR(100),
    browser VARCHAR(50),
    os VARCHAR(50),
    device VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- 5. FLIGHT SEARCHES
-- ===========================================
CREATE TABLE flight_searches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    origin VARCHAR(100),
    destination VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- 6. WEATHER SEARCHES
-- ===========================================
CREATE TABLE weather_searches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- 7. AI CONVERSATIONS
-- ===========================================
CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- 8. AI MESSAGES
-- ===========================================
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT,
    sender VARCHAR(20),
    text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- when you log in as a normal user and want to make yourself admin:-- 
UPDATE user
SET is_admin = 1
WHERE email = 'bhaveshmulchandani651@gmail.com';
