-- ============================================
-- EduTrackX — Database Setup
-- Student Result Management System
-- ============================================
-- Run this file in MySQL to create the database,
-- tables, and seed data.
--
-- Usage:
--   mysql -u root -p < database.sql
-- ============================================

-- Create the database
CREATE DATABASE IF NOT EXISTS edutrackx
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE edutrackx;

-- ============================================
-- Table: admin
-- Stores admin login credentials
-- ============================================
CREATE TABLE IF NOT EXISTS admin (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,  -- Stores werkzeug hashed password
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================
-- Table: students
-- Stores student information
-- ============================================
CREATE TABLE IF NOT EXISTS students (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    roll_no          VARCHAR(30)  NOT NULL UNIQUE,
    class            VARCHAR(50)  NOT NULL,
    password         VARCHAR(255) NOT NULL,
    email            VARCHAR(100) DEFAULT NULL,
    phone            VARCHAR(20)  DEFAULT NULL,
    dob              VARCHAR(20)  DEFAULT NULL,
    address          VARCHAR(255) DEFAULT NULL,
    current_semester INT          DEFAULT 1,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_roll_no (roll_no)
) ENGINE=InnoDB;

-- ============================================
-- Table: marks
-- Stores subject-wise marks for each student
-- ============================================
CREATE TABLE IF NOT EXISTS marks (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT          NOT NULL,
    subject     VARCHAR(100) NOT NULL,
    marks       INT          NOT NULL CHECK (marks >= 0 AND marks <= 100),
    semester    INT          DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_subject (student_id, subject)
) ENGINE=InnoDB;

-- ============================================
-- Table: exam_forms
-- Stores submitted exam enrollment forms
-- ============================================
CREATE TABLE IF NOT EXISTS exam_forms (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT          NOT NULL,
    semester    INT          NOT NULL,
    status      VARCHAR(20)  DEFAULT 'approved',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_semester_form (student_id, semester)
) ENGINE=InnoDB;

-- ============================================
-- Table: exam_form_subjects
-- Stores subjects chosen per exam form
-- ============================================
CREATE TABLE IF NOT EXISTS exam_form_subjects (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    form_id      INT          NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    exam_date    VARCHAR(20)  DEFAULT NULL,

    FOREIGN KEY (form_id) REFERENCES exam_forms(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- Table: migration_requests
-- Migration certificate applications
-- ============================================
CREATE TABLE IF NOT EXISTS migration_requests (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    student_id   INT          NOT NULL,
    destination  VARCHAR(200) NOT NULL,
    reason       TEXT         NOT NULL,
    status       VARCHAR(20)  DEFAULT 'pending',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB;
