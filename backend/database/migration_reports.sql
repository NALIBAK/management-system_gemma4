-- ============================================================
-- Migration: Report Generation Support
-- Adds columns and tables needed for comprehensive reports
-- Run this AFTER the base schema.sql has been applied
-- ============================================================

USE college_management;

-- 1. Add student_category and caste_community to student table
ALTER TABLE student
    ADD COLUMN IF NOT EXISTS student_category ENUM('centac','management','regular') DEFAULT 'regular' AFTER admission_type,
    ADD COLUMN IF NOT EXISTS caste_community VARCHAR(50) DEFAULT NULL AFTER student_category;

-- 2. Extracurricular Activity table
CREATE TABLE IF NOT EXISTS extracurricular_activity (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    activity_type ENUM('technical','non_technical') NOT NULL,
    category VARCHAR(100),                          -- e.g. hackathon, sports, cultural, paper, workshop
    event_date DATE,
    description TEXT,
    achievement VARCHAR(255),                       -- e.g. 1st Place, Participation, Published
    academic_year_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 3. Eligibility Criteria definition table
CREATE TABLE IF NOT EXISTS eligibility_criteria (
    criteria_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    criteria_type ENUM('cgpa','attendance','fee','backlog','other') NOT NULL,
    threshold_value FLOAT,                          -- e.g. 7.0 for CGPA, 75 for attendance %
    comparison ENUM('>=','<=','>','<','=') DEFAULT '>=',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Student ↔ Eligibility mapping table
CREATE TABLE IF NOT EXISTS student_eligibility (
    mapping_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    criteria_id INT NOT NULL,
    status ENUM('match','unmatch') NOT NULL,
    evaluated_value FLOAT,                          -- actual student value at time of evaluation
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks VARCHAR(255),
    UNIQUE KEY unique_elig (student_id, criteria_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (criteria_id) REFERENCES eligibility_criteria(criteria_id)
);

-- ============================================================
-- Seed Data for new tables
-- ============================================================

-- Sample Eligibility Criteria
INSERT IGNORE INTO eligibility_criteria (criteria_id, name, criteria_type, threshold_value, comparison, description) VALUES
(1, 'Minimum CGPA for Placement',    'cgpa',       7.0,  '>=', 'Student must have CGPA >= 7.0 to be eligible for campus placement'),
(2, 'Minimum Attendance',            'attendance',  75.0, '>=', 'Student must have >= 75% attendance'),
(3, 'No Fee Dues',                   'fee',         0.0,  '=',  'Student must have zero pending fee balance'),
(4, 'CGPA for Higher Studies',       'cgpa',        8.0,  '>=', 'Minimum CGPA 8.0 for higher studies recommendation'),
(5, 'Minimum CGPA for Scholarship',  'cgpa',        6.5,  '>=', 'CGPA >= 6.5 required to retain scholarship');
