from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required, hash_password
from app.utils.response import success, error
from app.utils.activity import log_activity

students_bp = Blueprint("students", __name__)

# --- Batches ---
@students_bp.route("/batches", methods=["GET"])
@login_required
def get_batches():
    return success(query("SELECT * FROM batch ORDER BY admission_year DESC"))

@students_bp.route("/batches", methods=["POST"])
@roles_required("super_admin", "admin")
def add_batch():
    data = request.get_json()
    bid = execute("INSERT INTO batch (college_id, admission_year, label) VALUES (%s,%s,%s)",
                  (data["college_id"], data["admission_year"], data["label"]))
    return success({"batch_id": bid}, "Batch created", 201)

# --- Sections ---
@students_bp.route("/sections", methods=["GET"])
@login_required
def get_sections():
    batch_id = request.args.get("batch_id")
    course_id = request.args.get("course_id")
    sql = """SELECT s.*, b.label as batch_label, c.name as course_name
             FROM section s JOIN batch b ON s.batch_id=b.batch_id
             JOIN course c ON s.course_id=c.course_id WHERE 1=1"""
    params = []
    if batch_id:
        sql += " AND s.batch_id=%s"; params.append(batch_id)
    if course_id:
        sql += " AND s.course_id=%s"; params.append(course_id)
    return success(query(sql, params))

@students_bp.route("/sections", methods=["POST"])
@roles_required("super_admin", "admin")
def add_section():
    data = request.get_json()
    sid = execute("INSERT INTO section (batch_id, course_id, name, current_semester) VALUES (%s,%s,%s,%s)",
                  (data["batch_id"], data["course_id"], data["name"], data.get("current_semester", 1)))
    return success({"section_id": sid}, "Section created", 201)

# --- Students ---
@students_bp.route("", methods=["GET"])
@login_required
def get_students():
    section_id = request.args.get("section_id")
    batch_id = request.args.get("batch_id")
    search = request.args.get("search", "")
    sql = """SELECT st.*, s.name as section_name, b.label as batch_label, c.name as course_name
             FROM student st
             JOIN section s ON st.section_id=s.section_id
             JOIN batch b ON st.batch_id=b.batch_id
             JOIN course c ON st.course_id=c.course_id WHERE 1=1"""
    params = []
    if section_id:
        sql += " AND st.section_id=%s"; params.append(section_id)
    if batch_id:
        sql += " AND st.batch_id=%s"; params.append(batch_id)
    if search:
        sql += " AND (st.name LIKE %s OR st.reg_number LIKE %s OR st.roll_number LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    return success(query(sql, params))

@students_bp.route("/<int:student_id>", methods=["GET"])
@login_required
def get_student(student_id):
    student = query("""SELECT st.*, s.name as section_name, c.name as course_name
                       FROM student st JOIN section s ON st.section_id=s.section_id
                       JOIN course c ON st.course_id=c.course_id
                       WHERE st.student_id=%s""", (student_id,), fetchone=True)
    if not student:
        return error("Student not found", 404)
    return success(student)

@students_bp.route("", methods=["POST"])
@roles_required("super_admin", "admin")
def add_student():
    data = request.get_json()
    sid = execute("""INSERT INTO student
        (reg_number, roll_number, name, email, phone, gender, dob, address, blood_group,
         guardian_name, guardian_phone, batch_id, section_id, course_id, admission_type,
         student_category, caste_community, admission_date, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (data["reg_number"], data["roll_number"], data["name"], data.get("email"),
         data.get("phone"), data.get("gender"), data.get("dob"), data.get("address"),
         data.get("blood_group"), data.get("guardian_name"), data.get("guardian_phone"),
         data["batch_id"], data["section_id"], data["course_id"],
         data.get("admission_type", "regular"),
         data.get("student_category", "regular"), data.get("caste_community"),
         data.get("admission_date"), data.get("status", "active")))

    log_activity(request.current_user["user_id"], "create", "student", sid, f"Added student {data['name']}")
    return success({"student_id": sid}, "Student added", 201)

@students_bp.route("/<int:student_id>", methods=["PUT"])
@roles_required("super_admin", "admin")
def update_student(student_id):
    data = request.get_json()
    execute("""UPDATE student SET name=%s, email=%s, phone=%s, gender=%s, dob=%s, address=%s,
               blood_group=%s, guardian_name=%s, guardian_phone=%s, section_id=%s,
               student_category=%s, caste_community=%s, status=%s
               WHERE student_id=%s""",
            (data["name"], data.get("email"), data.get("phone"), data.get("gender"),
             data.get("dob"), data.get("address"), data.get("blood_group"),
             data.get("guardian_name"), data.get("guardian_phone"),
             data["section_id"],
             data.get("student_category", "regular"), data.get("caste_community"),
             data.get("status", "active"), student_id))
    log_activity(request.current_user["user_id"], "update", "student", student_id, f"Updated student {data['name']}")
    return success(message="Student updated")

@students_bp.route("/<int:student_id>", methods=["DELETE"])
@roles_required("super_admin", "admin")
def delete_student(student_id):
    execute("UPDATE student SET status='inactive' WHERE student_id=%s", (student_id,))
    log_activity(request.current_user["user_id"], "delete", "student", student_id, "Deactivated student")
    return success(message="Student deactivated")
