-- ============================================================
-- College Management System — Database Schema
-- Run this in XAMPP phpMyAdmin or MySQL CLI
-- ============================================================

CREATE DATABASE IF NOT EXISTS college_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE college_management;

-- 1. College
CREATE TABLE IF NOT EXISTS college (
    college_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    logo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Academic Year
CREATE TABLE IF NOT EXISTS academic_year (
    academic_year_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id INT NOT NULL,
    year_label VARCHAR(20) NOT NULL,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (college_id) REFERENCES college(college_id)
);

-- 3. Department
CREATE TABLE IF NOT EXISTS department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    hod_staff_id INT,
    FOREIGN KEY (college_id) REFERENCES college(college_id)
);

-- 4. Course
CREATE TABLE IF NOT EXISTS course (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    code VARCHAR(20),
    total_semesters INT DEFAULT 8,
    degree_type VARCHAR(50),
    FOREIGN KEY (department_id) REFERENCES department(department_id)
);

-- 5. Semester
CREATE TABLE IF NOT EXISTS semester (
    semester_id INT AUTO_INCREMENT PRIMARY KEY,
    academic_year_id INT NOT NULL,
    semester_number INT NOT NULL,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 6. Subject
CREATE TABLE IF NOT EXISTS subject (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    semester_number INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    code VARCHAR(20),
    credits INT DEFAULT 3,
    type ENUM('theory','lab','project') DEFAULT 'theory',
    department_id INT,
    FOREIGN KEY (course_id) REFERENCES course(course_id),
    FOREIGN KEY (department_id) REFERENCES department(department_id)
);

-- 7. Batch
CREATE TABLE IF NOT EXISTS batch (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id INT NOT NULL,
    admission_year INT NOT NULL,
    label VARCHAR(50),
    FOREIGN KEY (college_id) REFERENCES college(college_id)
);

-- 8. Section
CREATE TABLE IF NOT EXISTS section (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    course_id INT NOT NULL,
    name VARCHAR(10) NOT NULL,
    current_semester INT DEFAULT 1,
    FOREIGN KEY (batch_id) REFERENCES batch(batch_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id)
);

-- 9. Staff
CREATE TABLE IF NOT EXISTS staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    gender ENUM('male','female','other'),
    designation VARCHAR(100),
    qualification VARCHAR(150),
    department_id INT,
    joining_date DATE,
    status ENUM('active','inactive') DEFAULT 'active',
    FOREIGN KEY (department_id) REFERENCES department(department_id)
);

-- Add HOD FK after staff table
ALTER TABLE department ADD CONSTRAINT fk_hod FOREIGN KEY (hod_staff_id) REFERENCES staff(staff_id);

-- 10. Student
CREATE TABLE IF NOT EXISTS student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    reg_number VARCHAR(50) UNIQUE NOT NULL,
    roll_number VARCHAR(20),
    name VARCHAR(150) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    gender ENUM('male','female','other'),
    dob DATE,
    address TEXT,
    blood_group VARCHAR(5),
    guardian_name VARCHAR(150),
    guardian_phone VARCHAR(20),
    batch_id INT NOT NULL,
    section_id INT NOT NULL,
    course_id INT NOT NULL,
    admission_type VARCHAR(50) DEFAULT 'regular',
    student_category ENUM('centac','management','regular') DEFAULT 'regular',
    caste_community VARCHAR(50) DEFAULT NULL,
    admission_date DATE,
    status ENUM('active','inactive','graduated','dropped') DEFAULT 'active',
    FOREIGN KEY (batch_id) REFERENCES batch(batch_id),
    FOREIGN KEY (section_id) REFERENCES section(section_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id)
);

-- 11. Role
CREATE TABLE IF NOT EXISTS role (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255)
);

-- 12. User Account
CREATE TABLE IF NOT EXISTS user_account (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    ref_id INT,
    ref_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES role(role_id)
);

-- 13. Activity Log
CREATE TABLE IF NOT EXISTS activity_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id INT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_account(user_id)
);

-- 14. Subject Allocation
CREATE TABLE IF NOT EXISTS subject_allocation (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    staff_id INT NOT NULL,
    subject_id INT NOT NULL,
    section_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    UNIQUE KEY unique_alloc (staff_id, subject_id, section_id, academic_year_id),
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id),
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id),
    FOREIGN KEY (section_id) REFERENCES section(section_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 15. Room
CREATE TABLE IF NOT EXISTS room (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    type ENUM('classroom','lab','seminar_hall','auditorium') DEFAULT 'classroom',
    capacity INT,
    building VARCHAR(100),
    floor_number INT,
    FOREIGN KEY (college_id) REFERENCES college(college_id)
);

-- 16. Period Definition
CREATE TABLE IF NOT EXISTS period_definition (
    period_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id INT NOT NULL,
    period_number INT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    label VARCHAR(50),
    FOREIGN KEY (college_id) REFERENCES college(college_id)
);

-- 17. Timetable
CREATE TABLE IF NOT EXISTS timetable (
    timetable_id INT AUTO_INCREMENT PRIMARY KEY,
    section_id INT NOT NULL,
    subject_id INT NOT NULL,
    staff_id INT NOT NULL,
    room_id INT,
    period_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    day_of_week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') NOT NULL,
    FOREIGN KEY (section_id) REFERENCES section(section_id),
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id),
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id),
    FOREIGN KEY (room_id) REFERENCES room(room_id),
    FOREIGN KEY (period_id) REFERENCES period_definition(period_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 18. Exam Type
CREATE TABLE IF NOT EXISTS exam_type (
    exam_type_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255)
);

-- 19. Exam
CREATE TABLE IF NOT EXISTS exam (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_type_id INT NOT NULL,
    subject_id INT NOT NULL,
    section_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    semester_id INT NOT NULL,
    exam_name VARCHAR(150) NOT NULL,
    exam_date DATE,
    max_marks FLOAT DEFAULT 100,
    passing_marks FLOAT DEFAULT 40,
    weightage_percent FLOAT DEFAULT 100,
    FOREIGN KEY (exam_type_id) REFERENCES exam_type(exam_type_id),
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id),
    FOREIGN KEY (section_id) REFERENCES section(section_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id),
    FOREIGN KEY (semester_id) REFERENCES semester(semester_id)
);

-- 20. Mark
CREATE TABLE IF NOT EXISTS mark (
    mark_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    marks_obtained FLOAT DEFAULT 0,
    is_absent BOOLEAN DEFAULT FALSE,
    remarks VARCHAR(255),
    UNIQUE KEY unique_mark (exam_id, student_id),
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id)
);

-- 21. Grade Mapping
CREATE TABLE IF NOT EXISTS grade_mapping (
    grade_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id INT NOT NULL,
    min_percentage FLOAT NOT NULL,
    max_percentage FLOAT NOT NULL,
    grade_letter VARCHAR(5) NOT NULL,
    grade_point FLOAT NOT NULL,
    FOREIGN KEY (college_id) REFERENCES college(college_id)
);

-- 22. Semester Result
CREATE TABLE IF NOT EXISTS semester_result (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    semester_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    total_credits FLOAT DEFAULT 0,
    credits_earned FLOAT DEFAULT 0,
    gpa FLOAT DEFAULT 0,
    cgpa FLOAT DEFAULT 0,
    is_manual_override BOOLEAN DEFAULT FALSE,
    result_status ENUM('pass','fail','pending') DEFAULT 'pending',
    UNIQUE KEY unique_result (student_id, semester_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (semester_id) REFERENCES semester(semester_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 23. Attendance
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    section_id INT NOT NULL,
    period_id INT,
    academic_year_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('P','A','OD','ML') DEFAULT 'A',
    remarks VARCHAR(255),
    UNIQUE KEY unique_att (student_id, subject_id, period_id, attendance_date),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id),
    FOREIGN KEY (section_id) REFERENCES section(section_id),
    FOREIGN KEY (period_id) REFERENCES period_definition(period_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 24. Fee Category
CREATE TABLE IF NOT EXISTS fee_category (
    fee_category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255)
);

-- 25. Fee Component
CREATE TABLE IF NOT EXISTS fee_component (
    component_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255)
);

-- 26. Fee Structure
CREATE TABLE IF NOT EXISTS fee_structure (
    fee_structure_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    fee_category_id INT NOT NULL,
    semester_number INT NOT NULL,
    academic_year_id INT NOT NULL,
    total_amount FLOAT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES course(course_id),
    FOREIGN KEY (fee_category_id) REFERENCES fee_category(fee_category_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 27. Fee Structure Detail
CREATE TABLE IF NOT EXISTS fee_structure_detail (
    detail_id INT AUTO_INCREMENT PRIMARY KEY,
    fee_structure_id INT NOT NULL,
    component_id INT NOT NULL,
    amount FLOAT NOT NULL,
    FOREIGN KEY (fee_structure_id) REFERENCES fee_structure(fee_structure_id),
    FOREIGN KEY (component_id) REFERENCES fee_component(component_id)
);

-- 28. Fee Payment
CREATE TABLE IF NOT EXISTS fee_payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    fee_structure_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    amount_paid FLOAT NOT NULL,
    payment_date DATE DEFAULT (CURRENT_DATE),
    payment_mode ENUM('cash','online','cheque','dd','upi') DEFAULT 'cash',
    receipt_number VARCHAR(50),
    transaction_ref VARCHAR(100),
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (fee_structure_id) REFERENCES fee_structure(fee_structure_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 29. Scholarship
CREATE TABLE IF NOT EXISTS scholarship (
    scholarship_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    scholarship_name VARCHAR(150) NOT NULL,
    amount FLOAT NOT NULL,
    status ENUM('pending','approved','rejected') DEFAULT 'pending',
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 30. AIRA Conversation
CREATE TABLE IF NOT EXISTS aira_conversation (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    page_context VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES user_account(user_id)
);

-- 31. AIRA Message
CREATE TABLE IF NOT EXISTS aira_message (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    role ENUM('user','assistant','system') NOT NULL,
    content TEXT,
    tool_calls TEXT,
    tool_results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES aira_conversation(conversation_id)
);

-- 32. AIRA Action Log
CREATE TABLE IF NOT EXISTS aira_action_log (
    action_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    conversation_id INT,
    action_type VARCHAR(100),
    entity_type VARCHAR(100),
    entity_id INT,
    action_details TEXT,
    status ENUM('success','error','pending') DEFAULT 'pending',
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_account(user_id)
);

-- 33. LLM Config
CREATE TABLE IF NOT EXISTS llm_config (
    config_id INT AUTO_INCREMENT PRIMARY KEY,
    college_id INT,
    provider VARCHAR(50) DEFAULT 'ollama',
    api_key_encrypted TEXT,
    selected_model VARCHAR(100) DEFAULT 'gemma3:1b',
    fallback_provider VARCHAR(50) DEFAULT 'ollama',
    fallback_model VARCHAR(100) DEFAULT 'gemma3:1b',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 2048,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 34. Notification Template
CREATE TABLE IF NOT EXISTS notification_template (
    template_id INT AUTO_INCREMENT PRIMARY KEY,
    staff_id INT,
    title VARCHAR(150) NOT NULL,
    content_template TEXT NOT NULL,
    channel_type ENUM('sms','whatsapp','email') DEFAULT 'email',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
);

-- 35. Notification Log
CREATE TABLE IF NOT EXISTS notification_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    sender_staff_id INT,
    channel_type ENUM('sms','whatsapp','email') DEFAULT 'email',
    message_content TEXT NOT NULL,
    status ENUM('sent','failed','pending') DEFAULT 'pending',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (sender_staff_id) REFERENCES staff(staff_id)
);

-- 36. Extracurricular Activity
CREATE TABLE IF NOT EXISTS extracurricular_activity (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    activity_type ENUM('technical','non_technical') NOT NULL,
    category VARCHAR(100),
    event_date DATE,
    description TEXT,
    achievement VARCHAR(255),
    academic_year_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- 37. Eligibility Criteria
CREATE TABLE IF NOT EXISTS eligibility_criteria (
    criteria_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    criteria_type ENUM('cgpa','attendance','fee','backlog','other') NOT NULL,
    threshold_value FLOAT,
    comparison ENUM('>=','<=','>','<','=') DEFAULT '>=',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 38. Student Eligibility Mapping
CREATE TABLE IF NOT EXISTS student_eligibility (
    mapping_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    criteria_id INT NOT NULL,
    status ENUM('match','unmatch') NOT NULL,
    evaluated_value FLOAT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks VARCHAR(255),
    UNIQUE KEY unique_elig (student_id, criteria_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (criteria_id) REFERENCES eligibility_criteria(criteria_id)
);
