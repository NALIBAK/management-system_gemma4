from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required
from app.utils.response import success, error

courses_bp = Blueprint("courses", __name__)

# --- Courses ---
@courses_bp.route("", methods=["GET"])
@login_required
def get_courses():
    dept_id = request.args.get("department_id")
    if dept_id:
        courses = query("SELECT * FROM course WHERE department_id=%s", (dept_id,))
    else:
        courses = query("SELECT c.*, d.name as department_name FROM course c JOIN department d ON c.department_id=d.department_id")
    return success(courses)

@courses_bp.route("", methods=["POST"])
@roles_required("super_admin", "admin")
def add_course():
    data = request.get_json()
    cid = execute(
        "INSERT INTO course (department_id, name, code, total_semesters, degree_type) VALUES (%s,%s,%s,%s,%s)",
        (data["department_id"], data["name"], data["code"], data["total_semesters"], data["degree_type"])
    )
    return success({"course_id": cid}, "Course created", 201)

@courses_bp.route("/<int:course_id>", methods=["PUT"])
@roles_required("super_admin", "admin")
def update_course(course_id):
    data = request.get_json()
    execute("UPDATE course SET name=%s, code=%s, total_semesters=%s, degree_type=%s WHERE course_id=%s",
            (data["name"], data["code"], data["total_semesters"], data["degree_type"], course_id))
    return success(message="Course updated")

@courses_bp.route("/<int:course_id>", methods=["DELETE"])
@roles_required("super_admin")
def delete_course(course_id):
    execute("DELETE FROM course WHERE course_id=%s", (course_id,))
    return success(message="Course deleted")

# --- Subjects ---
@courses_bp.route("/subjects", methods=["GET"])
@login_required
def get_subjects():
    course_id = request.args.get("course_id")
    semester = request.args.get("semester_number")
    sql = "SELECT s.*, c.name as course_name FROM subject s JOIN course c ON s.course_id=c.course_id WHERE 1=1"
    params = []
    if course_id:
        sql += " AND s.course_id=%s"
        params.append(course_id)
    if semester:
        sql += " AND s.semester_number=%s"
        params.append(semester)
    return success(query(sql, params))

@courses_bp.route("/subjects", methods=["POST"])
@roles_required("super_admin", "admin", "hod")
def add_subject():
    data = request.get_json()
    
    # Gracefully accept both 'semester' and 'semester_number'
    semester_num = data.get("semester_number", data.get("semester"))
    if not semester_num:
        return error("Semester is required", 400)
        
    sid = execute(
        "INSERT INTO subject (course_id, semester_number, name, code, credits, type, department_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (data["course_id"], semester_num, data["name"], data["code"],
         data.get("credits", 3), data.get("type", "theory"), data.get("department_id"))
    )
    return success({"subject_id": sid}, "Subject created", 201)

@courses_bp.route("/subjects/<int:subject_id>", methods=["PUT"])
@roles_required("super_admin", "admin", "hod")
def update_subject(subject_id):
    data = request.get_json()
    execute("UPDATE subject SET name=%s, code=%s, credits=%s, type=%s WHERE subject_id=%s",
            (data["name"], data["code"], data["credits"], data["type"], subject_id))
    return success(message="Subject updated")

@courses_bp.route("/subjects/<int:subject_id>", methods=["DELETE"])
@roles_required("super_admin", "admin")
def delete_subject(subject_id):
    execute("DELETE FROM subject WHERE subject_id=%s", (subject_id,))
    return success(message="Subject deleted")

# --- Semesters ---
@courses_bp.route("/semesters", methods=["GET"])
@login_required
def get_semesters():
    ay_id = request.args.get("academic_year_id")
    if ay_id:
        semesters = query("SELECT * FROM semester WHERE academic_year_id=%s ORDER BY semester_number", (ay_id,))
    else:
        semesters = query("SELECT * FROM semester ORDER BY academic_year_id, semester_number")
    return success(semesters)

@courses_bp.route("/semesters", methods=["POST"])
@roles_required("super_admin", "admin")
def add_semester():
    data = request.get_json()
    sid = execute(
        "INSERT INTO semester (academic_year_id, semester_number, start_date, end_date, is_current) VALUES (%s,%s,%s,%s,%s)",
        (data["academic_year_id"], data["semester_number"], data["start_date"], data["end_date"], data.get("is_current", False))
    )
    return success({"semester_id": sid}, "Semester created", 201)
