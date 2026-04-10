from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required
from app.utils.response import success, error

college_bp = Blueprint("college", __name__)

# --- College ---
@college_bp.route("/", methods=["GET"])
@login_required
def get_college():
    college = query("SELECT * FROM college LIMIT 1", fetchone=True)
    return success(college)

@college_bp.route("/", methods=["PUT"])
@roles_required("super_admin", "admin")
def update_college():
    data = request.get_json()
    execute("""UPDATE college SET name=%s, code=%s, address=%s, phone=%s, email=%s, logo_url=%s
               WHERE college_id=%s""",
            (data.get("name"), data.get("code"), data.get("address"),
             data.get("phone"), data.get("email"), data.get("logo_url"),
             data.get("college_id")))
    return success(message="College updated")

# --- Departments ---
@college_bp.route("/departments", methods=["GET"])
@login_required
def get_departments():
    depts = query("""SELECT d.*, s.name as hod_name FROM department d
                     LEFT JOIN staff s ON d.hod_staff_id = s.staff_id""")
    return success(depts)

@college_bp.route("/departments", methods=["POST"])
@roles_required("super_admin", "admin")
def add_department():
    data = request.get_json()
    dept_id = execute(
        "INSERT INTO department (college_id, name, code, hod_staff_id) VALUES (%s,%s,%s,%s)",
        (data.get("college_id", 1), data["name"], data["code"], data.get("hod_staff_id"))
    )
    return success({"department_id": dept_id}, "Department created", 201)

@college_bp.route("/departments/<int:dept_id>", methods=["PUT"])
@roles_required("super_admin", "admin")
def update_department(dept_id):
    data = request.get_json()
    execute("UPDATE department SET name=%s, code=%s, hod_staff_id=%s WHERE department_id=%s",
            (data["name"], data["code"], data.get("hod_staff_id"), dept_id))
    return success(message="Department updated")

@college_bp.route("/departments/<int:dept_id>", methods=["DELETE"])
@roles_required("super_admin")
def delete_department(dept_id):
    execute("DELETE FROM department WHERE department_id=%s", (dept_id,))
    return success(message="Department deleted")

# --- Academic Years ---
@college_bp.route("/academic-years", methods=["GET"])
@login_required
def get_academic_years():
    years = query("SELECT * FROM academic_year ORDER BY start_date DESC")
    return success(years)

@college_bp.route("/academic-years", methods=["POST"])
@roles_required("super_admin", "admin")
def add_academic_year():
    data = request.get_json()
    ay_id = execute(
        "INSERT INTO academic_year (college_id, year_label, start_date, end_date, is_current) VALUES (%s,%s,%s,%s,%s)",
        (data.get("college_id", 1), data["year_label"], data["start_date"], data["end_date"], data.get("is_current", False))
    )
    return success({"academic_year_id": ay_id}, "Academic year created", 201)

# --- Roles ---
@college_bp.route("/roles", methods=["GET"])
@login_required
def get_roles():
    roles = query("SELECT * FROM role")
    return success(roles)
