"""
===========================================================================
College Management System — Comprehensive Database Population Script
===========================================================================
Simulates a complete Engineering College with:
  - 6 Departments, 12 Courses, ~480 Subjects
  - 4-year batch cycle (2022-2026)
  - 1500 Students across all departments/sections
  - 150 Staff members
  - Attendance records, Marks, Fee structures/payments
  - Scholarships, Extracurricular activities, Eligibility criteria
  - Timetable, Rooms, Notification templates
  - Grade mappings, Semester results

Usage:  python populate_db.py
        (Make sure XAMPP MySQL is running)
===========================================================================
"""

import pymysql
import pymysql.cursors
import random
import string
import sys
from datetime import date, timedelta, datetime

# ---------- CONFIG ----------
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "college_management"

# ---------- CONNECTION ----------
def get_conn():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=False
    )

def run(conn, sql, params=None, many=False):
    """Execute query. Returns lastrowid for INSERT, or None."""
    with conn.cursor() as cur:
        if many:
            cur.executemany(sql, params)
        else:
            cur.execute(sql, params or ())
        return cur.lastrowid

# ---------- HELPERS ----------
FIRST_NAMES_M = [
    "Arun","Balaji","Chandru","Deepak","Ezhil","Ganesh","Hari","Ishaan","Jagan","Karthik",
    "Lokesh","Manoj","Naveen","Omkar","Pranav","Rahul","Sathish","Tharun","Uday","Vignesh",
    "Ajay","Bhuvan","Dinesh","Elango","Gokul","Harish","Jai","Kavin","Lakshmanan","Mohan",
    "Nithish","Prem","Ravi","Sanjay","Tarun","Varun","Ashwin","Bharath","Dhinesh","Gowtham",
    "Hemanth","Jagadeesh","Kiran","Logesh","Muthukumar","Nandha","Pradeep","Raghu","Saravanan","Vijay"
]
FIRST_NAMES_F = [
    "Anitha","Bharathi","Chitra","Divya","Eswari","Fathima","Gayathri","Hema","Indira","Janani",
    "Kavitha","Lakshmi","Meena","Nithya","Oviya","Priya","Ramya","Saranya","Tamilselvi","Uma",
    "Abinaya","Brindha","Dharani","Gomathi","Harini","Iswarya","Jayanthi","Keerthana","Lavanya","Malathi",
    "Nisha","Pavithra","Revathi","Sangeetha","Thenmozhi","Vaishnavi","Aishwarya","Deepika","Gowri","Haripriya",
    "Jenifer","Kokila","Madhumitha","Nandhini","Pooja","Radhika","Swetha","Vasanthi","Yamuna","Suganya"
]
LAST_NAMES = [
    "Kumar","Raj","Selvam","Murugan","Pandian","Rajan","Krishnan","Subramanian","Venkatesh","Narayanan",
    "Shankar","Prakash","Durai","Velan","Arumugam","Balasubramanian","Chelladurai","Devaraj","Govindaraj","Jayaraman",
    "Kannan","Lakshminarayanan","Mahalingam","Natarajan","Palani","Ramasamy","Senthil","Thirunavukkarasu","Velu","Sundaram"
]
BLOOD_GROUPS = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
CASTES = ["SC","ST","MBC","OBC","BC","OC"]
STUDENT_CATEGORIES = ["centac","management"]
GENDERS = ["male","female"]
DESIGNATIONS = ["Professor","Associate Professor","Assistant Professor","Lecturer","Lab Instructor"]
QUALIFICATIONS = ["Ph.D","M.Tech","M.E","M.Sc","M.Phil","MBA","B.Tech"]
BUILDINGS = ["Main Block","Science Block","Engineering Block","Workshop Block","Admin Block"]

TECHNICAL_EVENTS = [
    "Hackathon 2023","CodeSprint","TechFest","RoboWars","Paper Presentation","Project Expo",
    "Coding Challenge","AI Workshop","IoT Summit","Cyber Security Meet","DataThon","AppDev Contest"
]
NON_TECH_EVENTS = [
    "Annual Sports Day","Cultural Fest","Debate Competition","Essay Writing","Quiz Competition",
    "Music Concert","Dance Show","Drama Performance","Photography Contest","Painting Exhibition",
    "Volleyball Tournament","Cricket Match"
]
SCHOLARSHIP_NAMES = [
    "SC/ST Scholarship","BC Scholarship","MBC Scholarship","Merit Scholarship",
    "Central Govt Scholarship","State Govt Scholarship","College Scholarship",
    "Minority Scholarship","First Generation Scholarship","Sports Scholarship"
]

# ---------- DEPARTMENT / COURSE / SUBJECT DATA -----------
DEPARTMENTS = [
    {"name": "Computer Science & Engineering", "code": "CSE"},
    {"name": "Information Technology", "code": "IT"},
    {"name": "Electronics & Communication Engineering", "code": "ECE"},
    {"name": "Electrical & Electronics Engineering", "code": "EEE"},
    {"name": "Mechanical Engineering", "code": "MECH"},
    {"name": "Civil Engineering", "code": "CIVIL"},
]

COURSES_PER_DEPT = [
    # Each dept gets 2 courses
    [{"name": "B.Tech Computer Science & Engineering", "code": "BTCSE", "total_semesters": 8, "degree_type": "B.Tech"},
     {"name": "M.Tech Computer Science", "code": "MTCSE", "total_semesters": 4, "degree_type": "M.Tech"}],
    [{"name": "B.Tech Information Technology", "code": "BTIT", "total_semesters": 8, "degree_type": "B.Tech"},
     {"name": "M.Tech Information Technology", "code": "MTIT", "total_semesters": 4, "degree_type": "M.Tech"}],
    [{"name": "B.Tech Electronics & Communication", "code": "BTECE", "total_semesters": 8, "degree_type": "B.Tech"},
     {"name": "M.Tech VLSI Design", "code": "MTVLSI", "total_semesters": 4, "degree_type": "M.Tech"}],
    [{"name": "B.Tech Electrical & Electronics", "code": "BTEEE", "total_semesters": 8, "degree_type": "B.Tech"},
     {"name": "M.Tech Power Systems", "code": "MTPS", "total_semesters": 4, "degree_type": "M.Tech"}],
    [{"name": "B.Tech Mechanical Engineering", "code": "BTMECH", "total_semesters": 8, "degree_type": "B.Tech"},
     {"name": "M.Tech Thermal Engineering", "code": "MTTHE", "total_semesters": 4, "degree_type": "M.Tech"}],
    [{"name": "B.Tech Civil Engineering", "code": "BTCIVIL", "total_semesters": 8, "degree_type": "B.Tech"},
     {"name": "M.Tech Structural Engineering", "code": "MTSTR", "total_semesters": 4, "degree_type": "M.Tech"}],
]

# Subjects per semester for B.Tech courses (generic)
BTECH_SUBJECTS = {
    1: [("Engineering Mathematics I","EM1","theory",4),("Engineering Physics","EP","theory",3),("Engineering Chemistry","EC","theory",3),
        ("Basic Electrical Engineering","BEE","theory",3),("Programming in C","PIC","theory",4),("Engineering Graphics","EG","lab",2),
        ("Physics Lab","PL","lab",1),("C Programming Lab","CPL","lab",2)],
    2: [("Engineering Mathematics II","EM2","theory",4),("Environmental Science","ES","theory",2),("Object Oriented Programming","OOP","theory",4),
        ("Digital Logic Design","DLD","theory",3),("Data Structures","DS","theory",4),("OOP Lab","OOPL","lab",2),
        ("Data Structures Lab","DSL","lab",2),("Digital Logic Lab","DLL","lab",1)],
    3: [("Discrete Mathematics","DM","theory",4),("Computer Organization","CO","theory",3),("Operating Systems","OS","theory",4),
        ("Database Management Systems","DBMS","theory",4),("Probability & Statistics","PS","theory",3),("OS Lab","OSL","lab",2),
        ("DBMS Lab","DBMSL","lab",2)],
    4: [("Design & Analysis of Algorithms","DAA","theory",4),("Computer Networks","CN","theory",4),("Software Engineering","SE","theory",3),
        ("Microprocessors","MP","theory",3),("Theory of Computation","TOC","theory",3),("CN Lab","CNL","lab",2),
        ("Algorithms Lab","DAAL","lab",2)],
    5: [("Compiler Design","CD","theory",4),("Artificial Intelligence","AI","theory",4),("Web Technologies","WT","theory",3),
        ("Information Security","IS","theory",3),("Elective I","EL1","theory",3),("Web Tech Lab","WTL","lab",2),
        ("AI Lab","AIL","lab",2)],
    6: [("Machine Learning","ML","theory",4),("Cloud Computing","CC","theory",3),("Mobile App Development","MAD","theory",3),
        ("Data Mining","DMN","theory",3),("Elective II","EL2","theory",3),("ML Lab","MLL","lab",2),
        ("Cloud Lab","CCL","lab",2)],
    7: [("Deep Learning","DL","theory",4),("Big Data Analytics","BDA","theory",3),("Internet of Things","IOT","theory",3),
        ("Elective III","EL3","theory",3),("Project Phase I","PP1","project",4),("IoT Lab","IOTL","lab",2)],
    8: [("Blockchain Technology","BT","theory",3),("Ethics in Computing","EIC","theory",2),("Elective IV","EL4","theory",3),
        ("Project Phase II","PP2","project",8)],
}


# =====================================================
# MAIN SCRIPT
# =====================================================
def main():
    conn = get_conn()
    print("=" * 60)
    print("  College Management System — Database Populator")
    print("=" * 60)

    # ---- STEP 0: DELETE ALL EXISTING DATA ----
    print("\n[STEP 0] Deleting all existing data...")
    # Disable FK checks for clean truncation
    run(conn, "SET FOREIGN_KEY_CHECKS = 0")
    tables = [
        "student_eligibility","eligibility_criteria","extracurricular_activity",
        "notification_log","notification_template",
        "aira_action_log","aira_message","aira_conversation","llm_config",
        "semester_result","mark","exam","exam_type",
        "attendance","timetable","period_definition","room",
        "fee_payment","fee_structure_detail","fee_structure","fee_component","fee_category",
        "scholarship","subject_allocation","grade_mapping",
        "activity_log","user_account","role",
        "student","section","batch","subject","course","semester","academic_year","department","staff","college"
    ]
    for t in tables:
        run(conn, f"TRUNCATE TABLE `{t}`")
    run(conn, "SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    print("   All tables truncated.")

    # ---- STEP 1: COLLEGE ----
    print("\n[STEP 1] Creating college...")
    run(conn, """INSERT INTO college (name, code, address, phone, email)
                 VALUES (%s,%s,%s,%s,%s)""",
        ("Rajiv Gandhi College of Engineering and Technology", "RGCET",
         "Puducherry", "0413-1234567", "admin@rgcet.ac.in"))
    conn.commit()
    college_id = 1
    print(f"   College created (ID: {college_id})")

    # ---- STEP 2: ACADEMIC YEARS (4 years) ----
    print("\n[STEP 2] Creating academic years (2022-2026)...")
    ay_ids = {}
    years = [("2022-2023","2022-06-01","2023-05-31"),
             ("2023-2024","2023-06-01","2024-05-31"),
             ("2024-2025","2024-06-01","2025-05-31"),
             ("2025-2026","2025-06-01","2026-05-31")]
    for label, start, end in years:
        is_current = 1 if label == "2025-2026" else 0
        run(conn, """INSERT INTO academic_year (college_id, year_label, start_date, end_date, is_current)
                     VALUES (%s,%s,%s,%s,%s)""", (college_id, label, start, end, is_current))
    conn.commit()
    rows = conn.cursor()
    rows.execute("SELECT academic_year_id, year_label FROM academic_year ORDER BY academic_year_id")
    for r in rows.fetchall():
        ay_ids[r["year_label"]] = r["academic_year_id"]
    print(f"   Created {len(ay_ids)} academic years: {list(ay_ids.keys())}")

    # ---- STEP 3: SEMESTERS (2 per academic year) ----
    print("\n[STEP 3] Creating semesters...")
    sem_ids = {}  # (ay_label, sem_num) -> semester_id
    for label, ay_id in ay_ids.items():
        y1 = int(label.split("-")[0])
        for sem_n in [1, 2]:
            if sem_n == 1:
                s_date = f"{y1}-06-01"
                e_date = f"{y1}-11-30"
            else:
                s_date = f"{y1}-12-01"
                e_date = f"{y1+1}-05-31"
            is_cur = 1 if (label == "2025-2026" and sem_n == 2) else 0
            run(conn, """INSERT INTO semester (academic_year_id, semester_number, start_date, end_date, is_current)
                         VALUES (%s,%s,%s,%s,%s)""", (ay_id, sem_n, s_date, e_date, is_cur))
    conn.commit()
    rows.execute("SELECT semester_id, academic_year_id, semester_number FROM semester")
    ay_id_to_label = {v: k for k, v in ay_ids.items()}
    for r in rows.fetchall():
        sem_ids[(ay_id_to_label[r["academic_year_id"]], r["semester_number"])] = r["semester_id"]
    print(f"   Created {len(sem_ids)} semesters")

    # ---- STEP 4: DEPARTMENTS ----
    print("\n[STEP 4] Creating departments...")
    dept_ids = []
    for d in DEPARTMENTS:
        run(conn, "INSERT INTO department (college_id, name, code) VALUES (%s,%s,%s)",
            (college_id, d["name"], d["code"]))
    conn.commit()
    rows.execute("SELECT department_id, code FROM department ORDER BY department_id")
    dept_map = {}
    for r in rows.fetchall():
        dept_ids.append(r["department_id"])
        dept_map[r["code"]] = r["department_id"]
    print(f"   Created {len(dept_ids)} departments")

    # ---- STEP 5: COURSES ----
    print("\n[STEP 5] Creating courses...")
    course_ids = []
    all_courses = []
    for i, dept_courses in enumerate(COURSES_PER_DEPT):
        for c in dept_courses:
            run(conn, """INSERT INTO course (department_id, name, code, total_semesters, degree_type)
                         VALUES (%s,%s,%s,%s,%s)""",
                (dept_ids[i], c["name"], c["code"], c["total_semesters"], c["degree_type"]))
            all_courses.append({**c, "department_idx": i})
    conn.commit()
    rows.execute("SELECT course_id, code, total_semesters, department_id FROM course ORDER BY course_id")
    course_map = {}
    for r in rows.fetchall():
        course_ids.append(r["course_id"])
        course_map[r["course_id"]] = r
    btech_course_ids = [cid for cid, c in course_map.items() if c["total_semesters"] == 8]
    print(f"   Created {len(course_ids)} courses ({len(btech_course_ids)} B.Tech + {len(course_ids)-len(btech_course_ids)} M.Tech)")

    # ---- STEP 6: SUBJECTS ----
    print("\n[STEP 6] Creating subjects...")
    subject_count = 0
    for cid in btech_course_ids:
        dept_id = course_map[cid]["department_id"]
        code_prefix = course_map[cid]["code"][:2]
        for sem_num, subs in BTECH_SUBJECTS.items():
            for s_name, s_code, s_type, credits in subs:
                run(conn, """INSERT INTO subject (course_id, semester_number, name, code, credits, type, department_id)
                             VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (cid, sem_num, s_name, f"{code_prefix}{s_code}", credits, s_type, dept_id))
                subject_count += 1
    # M.Tech subjects (4 semesters, 4 subjects each)
    mtech_subjects = [
        ("Advanced Algorithms","AA","theory",4),("Research Methodology","RM","theory",3),
        ("Advanced DBMS","ADBMS","theory",4),("Seminar","SEM","project",2),
        ("Machine Learning","ML","theory",4),("Distributed Systems","DS","theory",3),
        ("Elective I","MEL1","theory",3),("Lab","MLAB1","lab",2),
        ("Thesis Phase I","TH1","project",6),("Elective II","MEL2","theory",3),
        ("Open Elective","MOE","theory",3),("Lab II","MLAB2","lab",2),
        ("Thesis Phase II","TH2","project",12),
    ]
    mtech_course_ids = [cid for cid in course_ids if cid not in btech_course_ids]
    for cid in mtech_course_ids:
        dept_id = course_map[cid]["department_id"]
        code_prefix = course_map[cid]["code"][:2]
        sem = 1
        for s_name, s_code, s_type, credits in mtech_subjects:
            run(conn, """INSERT INTO subject (course_id, semester_number, name, code, credits, type, department_id)
                         VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (cid, sem, s_name, f"{code_prefix}{s_code}", credits, s_type, dept_id))
            subject_count += 1
            if s_code in ["SEM","MLAB1","MLAB2"]:
                sem += 1
    conn.commit()
    print(f"   Created {subject_count} subjects")

    # Load subject map
    rows.execute("SELECT subject_id, course_id, semester_number, name FROM subject")
    all_subjects = rows.fetchall()
    subjects_by_course_sem = {}
    for s in all_subjects:
        key = (s["course_id"], s["semester_number"])
        subjects_by_course_sem.setdefault(key, []).append(s)

    # ---- STEP 7: ROLES & SUPERADMIN ----
    print("\n[STEP 7] Creating roles & superadmin...")
    roles = [("super_admin","Full system access"),("admin","College admin"),("hod","Department head"),
             ("staff","Teaching staff"),("student","Student access")]
    for rn, desc in roles:
        run(conn, "INSERT INTO role (role_name, description) VALUES (%s,%s)", (rn, desc))
    conn.commit()
    rows.execute("SELECT role_id, role_name FROM role")
    role_map = {r["role_name"]: r["role_id"] for r in rows.fetchall()}
    # bcrypt hash for Admin@123
    admin_hash = "$2b$12$LJ3m4ys6Gx8e4RFaKqZOluAGqRHMRFmJy/JO3eJjdiTVRGJqsmCa."
    run(conn, """INSERT INTO user_account (username, password_hash, role_id, is_active)
                 VALUES (%s,%s,%s,1)""", ("superadmin", admin_hash, role_map["super_admin"]))
    conn.commit()
    print(f"   Created {len(roles)} roles + superadmin account")

    # ---- STEP 8: BATCHES (4 years) ----
    print("\n[STEP 8] Creating batches (2022-2025)...")
    batch_ids = {}
    for yr in [2022, 2023, 2024, 2025]:
        run(conn, "INSERT INTO batch (college_id, admission_year, label) VALUES (%s,%s,%s)",
            (college_id, yr, f"Batch {yr}"))
    conn.commit()
    rows.execute("SELECT batch_id, admission_year FROM batch ORDER BY batch_id")
    for r in rows.fetchall():
        batch_ids[r["admission_year"]] = r["batch_id"]
    print(f"   Created {len(batch_ids)} batches")

    # ---- STEP 9: SECTIONS ----
    print("\n[STEP 9] Creating sections...")
    section_count = 0
    section_map = {}  # (batch_year, course_id, section_name) -> section_id
    for yr, bid in batch_ids.items():
        for cid in btech_course_ids:
            current_sem = min((2026 - yr) * 2, 8)
            for sec_name in ["A", "B"]:
                run(conn, """INSERT INTO section (batch_id, course_id, name, current_semester)
                             VALUES (%s,%s,%s,%s)""", (bid, cid, sec_name, current_sem))
                section_count += 1
        for cid in mtech_course_ids:
            if yr >= 2024:
                current_sem = min((2026 - yr) * 2, 4)
                run(conn, """INSERT INTO section (batch_id, course_id, name, current_semester)
                             VALUES (%s,%s,%s,%s)""", (bid, cid, "A", current_sem))
                section_count += 1
    conn.commit()
    rows.execute("SELECT section_id, batch_id, course_id, name FROM section")
    for r in rows.fetchall():
        bid_year = [yr for yr, bid in batch_ids.items() if bid == r["batch_id"]][0]
        section_map[(bid_year, r["course_id"], r["name"])] = r["section_id"]
    print(f"   Created {section_count} sections")

    # ---- STEP 10: STAFF (150) ----
    print("\n[STEP 10] Creating 150 staff members...")
    staff_ids_by_dept = {did: [] for did in dept_ids}
    staff_rows = []
    for i in range(150):
        dept_id = dept_ids[i % len(dept_ids)]
        gender = random.choice(GENDERS)
        fname = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
        lname = random.choice(LAST_NAMES)
        name = f"Dr. {fname} {lname}" if i < 30 else f"{fname} {lname}"
        emp_id = f"EMP{i+1:04d}"
        email = f"{fname.lower()}.{lname.lower()}{i}@rgcet.ac.in"
        phone = f"98{random.randint(10000000,99999999)}"
        desig = DESIGNATIONS[min(i // 30, len(DESIGNATIONS)-1)]
        qual = random.choice(QUALIFICATIONS)
        join_yr = random.randint(2015, 2024)
        join_date = f"{join_yr}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        staff_rows.append((emp_id, name, email, phone, gender, desig, qual, dept_id, join_date, "active"))
    run(conn, """INSERT INTO staff (employee_id, name, email, phone, gender, designation, qualification,
                 department_id, joining_date, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        staff_rows, many=True)
    conn.commit()
    rows.execute("SELECT staff_id, department_id, name FROM staff ORDER BY staff_id")
    all_staff = rows.fetchall()
    for s in all_staff:
        staff_ids_by_dept[s["department_id"]].append(s["staff_id"])
    # Create user accounts for staff
    staff_user_rows = []
    for s in all_staff:
        staff_user_rows.append((f"staff{s['staff_id']}", admin_hash, role_map["staff"], s["staff_id"], "staff", 1))
    run(conn, """INSERT INTO user_account (username, password_hash, role_id, ref_id, ref_type, is_active)
                 VALUES (%s,%s,%s,%s,%s,%s)""", staff_user_rows, many=True)
    conn.commit()
    # Set HODs (first staff in each dept)
    for did in dept_ids:
        if staff_ids_by_dept[did]:
            hod_id = staff_ids_by_dept[did][0]
            run(conn, "UPDATE department SET hod_staff_id=%s WHERE department_id=%s", (hod_id, did))
    conn.commit()
    print(f"   Created 150 staff + user accounts, assigned HODs")

    # ---- STEP 11: STUDENTS (1500) ----
    print("\n[STEP 11] Creating 1500 students...")
    student_rows = []
    students_per_section = {}
    student_counter = 0

    # Distribute: ~250 per B.Tech batch year (4 years x ~250 = 1000 for B.Tech)
    # ~125 per M.Tech batch year (2 years x ~125 = 250 for M.Tech)
    # Total ~1500

    # Collect all section keys for B.Tech
    btech_sections = [(yr, cid, sname)
                      for yr in batch_ids for cid in btech_course_ids
                      for sname in ["A","B"] if (yr, cid, sname) in section_map]
    mtech_sections = [(yr, cid, "A")
                      for yr in batch_ids for cid in mtech_course_ids
                      if (yr, cid, "A") in section_map]

    target_btech = 1250
    target_mtech = 250
    per_btech_sec = max(1, target_btech // len(btech_sections)) if btech_sections else 0
    per_mtech_sec = max(1, target_mtech // len(mtech_sections)) if mtech_sections else 0

    def make_students(sections, per_sec, start_idx):
        nonlocal student_counter
        rows_out = []
        for yr, cid, sname in sections:
            sid = section_map[(yr, cid, sname)]
            bid = batch_ids[yr]
            for j in range(per_sec):
                student_counter += 1
                idx = start_idx + student_counter
                gender = random.choice(GENDERS)
                fname = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
                lname = random.choice(LAST_NAMES)
                name = f"{fname} {lname}"
                reg = f"REG{yr}{idx:05d}"
                roll = f"{course_map[cid]['code']}{yr%100}{sname}{j+1:03d}"
                email = f"{fname.lower()}{idx}@student.rgcet.ac.in"
                phone = f"97{random.randint(10000000,99999999)}"
                dob_year = yr - random.randint(17, 20)
                dob = f"{dob_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                address = f"{random.randint(1,500)}, {random.choice(['Anna Nagar','T Nagar','Adyar','Velachery','Tambaram','Porur','Guindy','Chromepet','Mylapore','Perambur'])}, Chennai"
                blood = random.choice(BLOOD_GROUPS)
                guardian = f"{random.choice(FIRST_NAMES_M)} {lname}"
                guardian_ph = f"96{random.randint(10000000,99999999)}"
                adm_type = random.choice(["regular","management","lateral"])
                s_cat = random.choice(STUDENT_CATEGORIES)
                caste = random.choice(CASTES)
                adm_date = f"{yr}-{random.choice([6,7,8]):02d}-{random.randint(1,28):02d}"
                status = "active" if yr >= 2024 else random.choice(["active","graduated"])
                rows_out.append((reg, roll, name, email, phone, gender, dob, address, blood,
                                 guardian, guardian_ph, bid, sid, cid, adm_type, s_cat, caste, adm_date, status))
                students_per_section.setdefault(sid, [])
        return rows_out

    student_rows.extend(make_students(btech_sections, per_btech_sec, 0))
    student_rows.extend(make_students(mtech_sections, per_mtech_sec, len(student_rows)))

    # Pad to exactly 1500 if needed
    while len(student_rows) < 1500:
        sec = random.choice(btech_sections)
        extra = make_students([sec], 1, len(student_rows))
        student_rows.extend(extra)
    student_rows = student_rows[:1500]

    run(conn, """INSERT INTO student (reg_number, roll_number, name, email, phone, gender, dob, address,
                 blood_group, guardian_name, guardian_phone, batch_id, section_id, course_id,
                 admission_type, student_category, caste_community, admission_date, status)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        student_rows, many=True)
    conn.commit()
    # Load student IDs by section
    rows.execute("SELECT student_id, section_id, course_id, name FROM student ORDER BY student_id")
    all_students = rows.fetchall()
    for s in all_students:
        students_per_section.setdefault(s["section_id"], []).append(s["student_id"])
    # Student user accounts
    stu_user_rows = [(f"stu{s['student_id']}", admin_hash, role_map["student"], s["student_id"], "student", 1)
                     for s in all_students]
    run(conn, """INSERT INTO user_account (username, password_hash, role_id, ref_id, ref_type, is_active)
                 VALUES (%s,%s,%s,%s,%s,%s)""", stu_user_rows, many=True)
    conn.commit()
    print(f"   Created {len(all_students)} students + user accounts")

    # ---- STEP 12: ROOMS ----
    print("\n[STEP 12] Creating rooms...")
    room_rows = []
    room_id_counter = 0
    for bldg in BUILDINGS[:3]:
        for floor in range(4):
            for rn in range(1, 7):
                room_id_counter += 1
                rtype = "lab" if rn > 4 else "classroom"
                cap = 60 if rtype == "classroom" else 30
                room_rows.append((college_id, f"{bldg[0]}{floor}{rn:02d}", rtype, cap, bldg, floor))
    run(conn, "INSERT INTO room (college_id, name, type, capacity, building, floor_number) VALUES (%s,%s,%s,%s,%s,%s)",
        room_rows, many=True)
    conn.commit()
    rows.execute("SELECT room_id FROM room")
    room_ids = [r["room_id"] for r in rows.fetchall()]
    print(f"   Created {len(room_ids)} rooms")

    # ---- STEP 13: PERIODS ----
    print("\n[STEP 13] Creating period definitions...")
    periods_data = [
        (1,"09:00","09:50","Period 1"),(2,"09:50","10:40","Period 2"),
        (3,"10:50","11:40","Period 3"),(4,"11:40","12:30","Period 4"),
        (5,"13:30","14:20","Period 5"),(6,"14:20","15:10","Period 6"),
        (7,"15:20","16:10","Period 7"),(8,"16:10","17:00","Period 8"),
    ]
    for pn, st, et, lbl in periods_data:
        run(conn, "INSERT INTO period_definition (college_id, period_number, start_time, end_time, label) VALUES (%s,%s,%s,%s,%s)",
            (college_id, pn, st, et, lbl))
    conn.commit()
    rows.execute("SELECT period_id, period_number FROM period_definition")
    period_map = {r["period_number"]: r["period_id"] for r in rows.fetchall()}
    print(f"   Created {len(period_map)} periods")

    # ---- STEP 14: EXAM TYPES ----
    print("\n[STEP 14] Creating exam types...")
    et_data = [("Internal Assessment 1","First internal exam"),("Internal Assessment 2","Second internal exam"),
               ("Internal Assessment 3","Third internal exam"),("End Semester","University end semester exam"),
               ("Lab Exam","Practical examination"),("Revaluation","Re-examination")]
    for n, d in et_data:
        run(conn, "INSERT INTO exam_type (name, description) VALUES (%s,%s)", (n, d))
    conn.commit()
    rows.execute("SELECT exam_type_id, name FROM exam_type")
    exam_type_map = {r["name"]: r["exam_type_id"] for r in rows.fetchall()}
    print(f"   Created {len(exam_type_map)} exam types")

    # ---- STEP 15: GRADE MAPPINGS ----
    print("\n[STEP 15] Creating grade mappings...")
    grades = [(90,100,"O",10),(80,89.99,"A+",9),(70,79.99,"A",8),(60,69.99,"B+",7),
              (50,59.99,"B",6),(45,49.99,"C",5),(40,44.99,"P",4),(0,39.99,"F",0)]
    for mn, mx, gl, gp in grades:
        run(conn, "INSERT INTO grade_mapping (college_id, min_percentage, max_percentage, grade_letter, grade_point) VALUES (%s,%s,%s,%s,%s)",
            (college_id, mn, mx, gl, gp))
    conn.commit()
    print(f"   Created {len(grades)} grade mappings")

    # ---- STEP 16: FEE CATEGORIES & COMPONENTS ----
    print("\n[STEP 16] Creating fee categories & components...")
    fee_cats = [("Tuition Fee","Regular tuition fee"),("Hostel Fee","Hostel accommodation"),
                ("Transport Fee","College transport"),("Lab Fee","Laboratory charges"),
                ("Exam Fee","Examination fee")]
    for n, d in fee_cats:
        run(conn, "INSERT INTO fee_category (name, description) VALUES (%s,%s)", (n, d))
    conn.commit()
    rows.execute("SELECT fee_category_id FROM fee_category")
    fee_cat_ids = [r["fee_category_id"] for r in rows.fetchall()]

    fee_comps = [("Tuition","Tuition fee component"),("Library","Library fee"),
                 ("Sports","Sports fee"),("Development","Infrastructure development"),
                 ("Insurance","Student insurance")]
    for n, d in fee_comps:
        run(conn, "INSERT INTO fee_component (name, description) VALUES (%s,%s)", (n, d))
    conn.commit()
    rows.execute("SELECT component_id FROM fee_component")
    comp_ids = [r["component_id"] for r in rows.fetchall()]
    print(f"   Created {len(fee_cat_ids)} fee categories, {len(comp_ids)} components")

    # ---- STEP 17: FEE STRUCTURES ----
    print("\n[STEP 17] Creating fee structures...")
    fs_count = 0
    for cid in course_ids:
        total_sems = course_map[cid]["total_semesters"]
        for ay_label, ay_id in ay_ids.items():
            for sem_n in range(1, total_sems + 1):
                base = 75000 if total_sems == 8 else 50000
                total_amt = base + random.randint(-5000, 10000)
                run(conn, """INSERT INTO fee_structure (course_id, fee_category_id, semester_number, academic_year_id, total_amount)
                             VALUES (%s,%s,%s,%s,%s)""",
                    (cid, fee_cat_ids[0], sem_n, ay_id, total_amt))
                fs_count += 1
    conn.commit()
    print(f"   Created {fs_count} fee structures")

    # ---- STEP 18: SUBJECT ALLOCATIONS + TIMETABLE ----
    print("\n[STEP 18] Creating subject allocations & timetable...")
    alloc_count = 0
    tt_count = 0
    current_ay = ay_ids["2025-2026"]
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday"]

    for (yr, cid, sname), sec_id in section_map.items():
        dept_id = course_map[cid]["department_id"]
        dept_staff = staff_ids_by_dept.get(dept_id, [])
        if not dept_staff:
            continue
        current_sem = min((2026 - yr) * 2, course_map[cid]["total_semesters"])
        subs = subjects_by_course_sem.get((cid, current_sem), [])
        for idx, sub in enumerate(subs):
            staff_id = dept_staff[idx % len(dept_staff)]
            try:
                run(conn, """INSERT INTO subject_allocation (staff_id, subject_id, section_id, academic_year_id)
                             VALUES (%s,%s,%s,%s)""", (staff_id, sub["subject_id"], sec_id, current_ay))
                alloc_count += 1
            except:
                pass
            # Timetable entry
            day = days[idx % len(days)]
            period = period_map.get((idx % 8) + 1, list(period_map.values())[0])
            room = random.choice(room_ids)
            try:
                run(conn, """INSERT INTO timetable (section_id, subject_id, staff_id, room_id, period_id, academic_year_id, day_of_week)
                             VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (sec_id, sub["subject_id"], staff_id, room, period, current_ay, day))
                tt_count += 1
            except:
                pass
    conn.commit()
    print(f"   Created {alloc_count} allocations, {tt_count} timetable entries")

    # ---- STEP 19: ATTENDANCE (sampled) ----
    print("\n[STEP 19] Creating attendance records (sampled — this takes a moment)...")
    att_count = 0
    att_rows = []
    # Generate ~30 days of attendance for current semester per section (sampled)
    sample_dates = [date(2025, 12, 1) + timedelta(days=d)
                    for d in range(90) if (date(2025, 12, 1) + timedelta(days=d)).weekday() < 5]
    sample_dates = sample_dates[:30]  # 30 working days

    for (yr, cid, sname), sec_id in section_map.items():
        if yr < 2024:
            continue  # Skip old batches for attendance
        current_sem = min((2026 - yr) * 2, course_map[cid]["total_semesters"])
        subs = subjects_by_course_sem.get((cid, current_sem), [])[:3]  # Only 3 subjects to keep size reasonable
        stu_list = students_per_section.get(sec_id, [])
        if not stu_list or not subs:
            continue
        for att_date in sample_dates[:10]:  # 10 days per section to keep manageable
            for sub in subs:
                for stu_id in stu_list:
                    status = random.choices(["P","A","OD"], weights=[85,12,3])[0]
                    att_rows.append((stu_id, sub["subject_id"], sec_id, period_map[1], current_ay,
                                    att_date.isoformat(), status))
                    att_count += 1
                    if len(att_rows) >= 5000:
                        run(conn, """INSERT INTO attendance (student_id, subject_id, section_id, period_id,
                                     academic_year_id, attendance_date, status)
                                     VALUES (%s,%s,%s,%s,%s,%s,%s)""", att_rows, many=True)
                        conn.commit()
                        att_rows = []
    if att_rows:
        run(conn, """INSERT INTO attendance (student_id, subject_id, section_id, period_id,
                     academic_year_id, attendance_date, status)
                     VALUES (%s,%s,%s,%s,%s,%s,%s)""", att_rows, many=True)
        conn.commit()
    print(f"   Created {att_count} attendance records")

    # ---- STEP 20: EXAMS & MARKS ----
    print("\n[STEP 20] Creating exams & marks...")
    exam_count = 0
    mark_count = 0
    mark_rows = []

    for (yr, cid, sname), sec_id in section_map.items():
        current_sem = min((2026 - yr) * 2, course_map[cid]["total_semesters"])
        subs = subjects_by_course_sem.get((cid, current_sem), [])
        stu_list = students_per_section.get(sec_id, [])
        if not stu_list or not subs:
            continue
        # Find matching semester_id
        ay_label = "2025-2026"
        sem_key = (ay_label, 2)  # Even semester
        s_id = sem_ids.get(sem_key)
        if not s_id:
            continue

        for sub in subs[:4]:  # Max 4 subjects per section for exams
            # Internal Assessment 1
            et_id = exam_type_map["Internal Assessment 1"]
            run(conn, """INSERT INTO exam (exam_type_id, subject_id, section_id, academic_year_id, semester_id,
                         exam_name, exam_date, max_marks, passing_marks, weightage_percent)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (et_id, sub["subject_id"], sec_id, current_ay, s_id,
                 f"IA1 - {sub['name']}", "2026-01-15", 50, 20, 20))
            exam_count += 1
            rows.execute("SELECT LAST_INSERT_ID() as eid")
            eid = rows.fetchone()["eid"]
            for stu_id in stu_list:
                marks = round(random.gauss(35, 10))
                marks = max(0, min(50, marks))
                is_absent = random.random() < 0.03
                mark_rows.append((eid, stu_id, 0 if is_absent else marks, is_absent, None))
                mark_count += 1
                if len(mark_rows) >= 5000:
                    run(conn, "INSERT INTO mark (exam_id, student_id, marks_obtained, is_absent, remarks) VALUES (%s,%s,%s,%s,%s)",
                        mark_rows, many=True)
                    conn.commit()
                    mark_rows = []
    if mark_rows:
        run(conn, "INSERT INTO mark (exam_id, student_id, marks_obtained, is_absent, remarks) VALUES (%s,%s,%s,%s,%s)",
            mark_rows, many=True)
        conn.commit()
    print(f"   Created {exam_count} exams, {mark_count} marks")

    # ---- STEP 21: FEE PAYMENTS ----
    print("\n[STEP 21] Creating fee payments...")
    payment_count = 0
    pay_rows = []
    rows.execute("SELECT fee_structure_id, course_id, academic_year_id, total_amount FROM fee_structure")
    all_fs = rows.fetchall()
    fs_by_course_ay = {}
    for fs in all_fs:
        fs_by_course_ay.setdefault((fs["course_id"], fs["academic_year_id"]), []).append(fs)

    for s in all_students[:1000]:  # Payments for 1000 students
        cid = s["course_id"]
        fs_list = fs_by_course_ay.get((cid, current_ay), [])
        if not fs_list:
            continue
        fs = fs_list[0]
        paid = random.choice([True, True, True, False])  # 75% paid
        if paid:
            amt = fs["total_amount"]
            mode = random.choice(["cash","online","upi","cheque"])
            receipt = f"RCP{payment_count+1:06d}"
            pay_date = f"2025-{random.randint(7,12):02d}-{random.randint(1,28):02d}"
            pay_rows.append((s["student_id"], fs["fee_structure_id"], current_ay, amt, pay_date, mode, receipt, None, None))
            payment_count += 1
            if len(pay_rows) >= 3000:
                run(conn, """INSERT INTO fee_payment (student_id, fee_structure_id, academic_year_id, amount_paid,
                             payment_date, payment_mode, receipt_number, transaction_ref, remarks)
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", pay_rows, many=True)
                conn.commit()
                pay_rows = []
    if pay_rows:
        run(conn, """INSERT INTO fee_payment (student_id, fee_structure_id, academic_year_id, amount_paid,
                     payment_date, payment_mode, receipt_number, transaction_ref, remarks)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", pay_rows, many=True)
        conn.commit()
    print(f"   Created {payment_count} fee payments")

    # ---- STEP 22: SCHOLARSHIPS ----
    print("\n[STEP 22] Creating scholarships...")
    schol_rows = []
    for s in random.sample(all_students, min(200, len(all_students))):
        name = random.choice(SCHOLARSHIP_NAMES)
        amount = random.choice([5000, 10000, 15000, 25000, 50000])
        status = random.choice(["pending","approved","approved","approved"])
        schol_rows.append((s["student_id"], current_ay, name, amount, status))
    run(conn, "INSERT INTO scholarship (student_id, academic_year_id, scholarship_name, amount, status) VALUES (%s,%s,%s,%s,%s)",
        schol_rows, many=True)
    conn.commit()
    print(f"   Created {len(schol_rows)} scholarships")

    # ---- STEP 23: EXTRACURRICULAR ACTIVITIES ----
    print("\n[STEP 23] Creating extracurricular activities...")
    act_rows = []
    for s in random.sample(all_students, min(300, len(all_students))):
        is_tech = random.random() < 0.5
        evt = random.choice(TECHNICAL_EVENTS if is_tech else NON_TECH_EVENTS)
        atype = "technical" if is_tech else "non_technical"
        cat = random.choice(["Competition","Workshop","Seminar","Cultural","Sports"])
        evt_date = f"{random.randint(2023,2025)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        achievement = random.choice(["1st Prize","2nd Prize","3rd Prize","Participation","Best Performance","Merit","None"])
        act_rows.append((s["student_id"], evt, atype, cat, evt_date, f"Participated in {evt}", achievement, current_ay))
    run(conn, """INSERT INTO extracurricular_activity (student_id, title, activity_type, category, event_date,
                 description, achievement, academic_year_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        act_rows, many=True)
    conn.commit()
    print(f"   Created {len(act_rows)} extracurricular activities")

    # ---- STEP 24: ELIGIBILITY CRITERIA ----
    print("\n[STEP 24] Creating eligibility criteria...")
    criteria = [
        ("Minimum CGPA 6.0","cgpa",6.0,">=","Minimum CGPA required for placements"),
        ("Minimum Attendance 75%","attendance",75.0,">=","Minimum attendance percentage"),
        ("No Fee Dues","fee",0.0,"=","All fees must be cleared"),
        ("No Active Backlogs","backlog",0.0,"=","Zero backlogs required"),
        ("CGPA >= 7.0 for Higher Studies","cgpa",7.0,">=","Minimum CGPA for MS/MTech recommendation"),
    ]
    for n, ct, tv, comp, desc in criteria:
        run(conn, """INSERT INTO eligibility_criteria (name, criteria_type, threshold_value, comparison, description)
                     VALUES (%s,%s,%s,%s,%s)""", (n, ct, tv, comp, desc))
    conn.commit()
    rows.execute("SELECT criteria_id FROM eligibility_criteria")
    criteria_ids = [r["criteria_id"] for r in rows.fetchall()]
    # Map some students
    elig_rows = []
    for s in random.sample(all_students, min(500, len(all_students))):
        for cri_id in criteria_ids:
            status = random.choice(["match","match","match","unmatch"])
            val = round(random.uniform(4.0, 9.5), 2)
            elig_rows.append((s["student_id"], cri_id, status, val, None))
    run(conn, """INSERT INTO student_eligibility (student_id, criteria_id, status, evaluated_value, remarks)
                 VALUES (%s,%s,%s,%s,%s)""", elig_rows, many=True)
    conn.commit()
    print(f"   Created {len(criteria)} criteria, {len(elig_rows)} eligibility mappings")

    # ---- STEP 25: NOTIFICATION TEMPLATES ----
    print("\n[STEP 25] Creating notification templates...")
    templates = [
        ("Fee Reminder","Dear {GuardianName}, this is a reminder that fees for {StudentName} ({RegNumber}) are pending. Please pay at the earliest.","email"),
        ("Attendance Warning","Dear {GuardianName}, your ward {StudentName} has attendance below 75%. Please ensure regular attendance.","sms"),
        ("Exam Schedule","Dear {StudentName}, your upcoming exams start from next week. Please prepare well.","email"),
        ("Result Published","Dear {GuardianName}, results for {StudentName} ({RegNumber}) have been published. Please check the portal.","whatsapp"),
        ("Holiday Notice","Dear {StudentName}, the college will remain closed on the upcoming holiday. Enjoy your break!","email"),
    ]
    hod_id = all_staff[0]["staff_id"]
    for title, content, channel in templates:
        run(conn, """INSERT INTO notification_template (staff_id, title, content_template, channel_type)
                     VALUES (%s,%s,%s,%s)""", (hod_id, title, content, channel))
    conn.commit()
    print(f"   Created {len(templates)} notification templates")

    # ---- STEP 26: LLM CONFIG ----
    print("\n[STEP 26] Creating LLM config...")
    run(conn, """INSERT INTO llm_config (college_id, provider, selected_model, fallback_provider, fallback_model, temperature, max_tokens)
                 VALUES (%s,'ollama','gemma3:1b','ollama','gemma3:1b',0.7,2048)""", (college_id,))
    conn.commit()
    print("   LLM config created")

    # ---- STEP 27: SEMESTER RESULTS ----
    print("\n[STEP 27] Creating semester results...")
    result_rows = []
    sem_key = ("2025-2026", 2)
    s_id = sem_ids.get(sem_key)
    if s_id:
        for s in all_students[:800]:
            total_credits = random.randint(18, 24)
            earned = random.randint(int(total_credits * 0.7), total_credits)
            gpa = round(random.uniform(5.0, 9.5), 2)
            cgpa = round(random.uniform(5.5, 9.2), 2)
            status = "pass" if gpa >= 4.0 else "fail"
            result_rows.append((s["student_id"], s_id, current_ay, total_credits, earned, gpa, cgpa, False, status))
    if result_rows:
        run(conn, """INSERT INTO semester_result (student_id, semester_id, academic_year_id, total_credits,
                     credits_earned, gpa, cgpa, is_manual_override, result_status)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", result_rows, many=True)
        conn.commit()
    print(f"   Created {len(result_rows)} semester results")

    # ---- DONE ----
    conn.close()
    print("\n" + "=" * 60)
    print("  ✅ DATABASE POPULATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"""
  Summary:
    🏛  College: Rajiv Gandhi College of Engineering and Technology
    📅  Academic Years: 4 (2022-2026)
    🏢  Departments: {len(DEPARTMENTS)}
    📚  Courses: {len(course_ids)}
    📖  Subjects: {subject_count}
    👨‍🏫  Staff: 150
    👨‍🎓  Students: {len(all_students)}
    📅  Attendance Records: {att_count}
    📝  Exams: {exam_count}
    📊  Marks: {mark_count}
    💰  Fee Payments: {payment_count}
    🎓  Scholarships: {len(schol_rows)}
    🏆  Extracurricular Activities: {len(act_rows)}
    ✅  Eligibility Mappings: {len(elig_rows)}
    📋  Semester Results: {len(result_rows)}
    🔔  Notification Templates: {len(templates)}

  Login: superadmin / Admin@123
""")


if __name__ == "__main__":
    main()
