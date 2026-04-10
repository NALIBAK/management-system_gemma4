USE college_management;

-- Roles
INSERT IGNORE INTO role (role_name, description) VALUES
('super_admin', 'Full system access'),
('admin', 'College administration access'),
('hod', 'Department head access'),
('staff', 'Teaching staff access');

-- Default College
INSERT IGNORE INTO college (college_id, name, code, address, phone, email) VALUES
(1, 'Your College Name', 'COL001', '123 College Road, City', '9876543210', 'admin@college.edu');

-- Default Academic Year
INSERT IGNORE INTO academic_year (academic_year_id, college_id, year_label, start_date, end_date, is_current) VALUES
(1, 1, '2024-25', '2024-07-01', '2025-06-30', TRUE);

-- Default Semester
INSERT IGNORE INTO semester (semester_id, academic_year_id, semester_number, start_date, end_date, is_current) VALUES
(1, 1, 1, '2024-07-01', '2024-11-30', TRUE),
(2, 1, 2, '2025-01-01', '2025-05-31', FALSE);

-- Grade Mapping (Anna University style)
INSERT IGNORE INTO grade_mapping (college_id, min_percentage, max_percentage, grade_letter, grade_point) VALUES
(1, 91, 100, 'O',  10.0),
(1, 81, 90,  'A+', 9.0),
(1, 71, 80,  'A',  8.0),
(1, 61, 70,  'B+', 7.0),
(1, 51, 60,  'B',  6.0),
(1, 45, 50,  'C',  5.0),
(1, 0,  44,  'U',  0.0);

-- Exam Types
INSERT IGNORE INTO exam_type (name, description) VALUES
('Internal', 'Internal assessment exam'),
('External', 'University external exam'),
('Assignment', 'Assignment submission'),
('Lab Practical', 'Laboratory practical exam');

-- Fee Categories
INSERT IGNORE INTO fee_category (name, description) VALUES
('Management Quota', 'Management quota students'),
('Government Quota', 'Government quota students'),
('SC/ST', 'SC/ST category students'),
('OBC', 'OBC category students');

-- Fee Components
INSERT IGNORE INTO fee_component (name, description) VALUES
('Tuition Fee', 'Academic tuition charges'),
('Lab Fee', 'Laboratory usage charges'),
('Library Fee', 'Library access charges'),
('Exam Fee', 'Examination charges'),
('Hostel Fee', 'Hostel accommodation'),
('Transport Fee', 'Bus/transport charges');

-- Period Definitions
INSERT IGNORE INTO period_definition (college_id, period_number, start_time, end_time, label) VALUES
(1, 1, '08:00:00', '08:50:00', 'Period 1'),
(1, 2, '08:50:00', '09:40:00', 'Period 2'),
(1, 3, '09:50:00', '10:40:00', 'Period 3'),
(1, 4, '10:40:00', '11:30:00', 'Period 4'),
(1, 5, '12:10:00', '13:00:00', 'Period 5'),
(1, 6, '13:00:00', '13:50:00', 'Period 6'),
(1, 7, '13:50:00', '14:40:00', 'Period 7');

-- Default Super Admin (password: Admin@123)
-- IMPORTANT: This hash was generated with Python's bcrypt library (bcrypt.hashpw)
-- DO NOT replace with a PHP-generated hash — they are incompatible with PyBcrypt
INSERT IGNORE INTO user_account (username, password_hash, role_id, ref_type, is_active) VALUES
('superadmin',
 '$2b$12$PSJNxtS1oLzv9NCrlRRrSeZZXfTQex2cJCMdXgdLx2rx/LklkKrYJS',
 (SELECT role_id FROM role WHERE role_name='super_admin'),
 'admin', 1);

-- LLM Config (defaults to Ollama with gemma3:1b — change in Settings → LLM Config)
-- Run: ollama pull gemma3:1b
-- Alternatively pull any model and update selected_model here or via the UI
INSERT IGNORE INTO llm_config (college_id, provider, selected_model, fallback_provider, fallback_model, temperature, max_tokens) VALUES
(1, 'ollama', 'gemma3:1b', 'ollama', 'gemma3:1b', 0.7, 2048);
