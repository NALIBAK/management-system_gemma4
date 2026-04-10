from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required, hash_password
from app.utils.response import success, error
from app.utils.activity import log_activity

staff_bp = Blueprint("staff", __name__)

@staff_bp.route("", methods=["GET"])
@login_required
def get_staff():
    dept_id = request.args.get("department_id")
    search = request.args.get("search", "")
    sql = """SELECT s.*, d.name as department_name FROM staff s
             LEFT JOIN department d ON s.department_id=d.department_id WHERE 1=1"""
    params = []
    if dept_id:
        sql += " AND s.department_id=%s"; params.append(dept_id)
    if search:
        sql += " AND (s.name LIKE %s OR s.employee_id LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    return success(query(sql, params))

@staff_bp.route("/<int:staff_id>", methods=["GET"])
@login_required
def get_staff_member(staff_id):
    member = query("""SELECT s.*, d.name as department_name FROM staff s
                      LEFT JOIN department d ON s.department_id=d.department_id
                      WHERE s.staff_id=%s""", (staff_id,), fetchone=True)
    if not member:
        return error("Staff not found", 404)
    return success(member)

@staff_bp.route("", methods=["POST"])
@roles_required("super_admin", "admin")
def add_staff():
    data = request.get_json()
    
    # Check if employee_id already exists
    existing = query("SELECT staff_id FROM staff WHERE employee_id=%s", (data["employee_id"],), fetchone=True)
    if existing:
        return error("Employee ID already exists", 400)

    sid = execute("""INSERT INTO staff
        (employee_id, name, email, phone, gender, designation, qualification, department_id, joining_date, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (data["employee_id"], data["name"], data.get("email"), data.get("phone"),
         data.get("gender"), data["designation"], data.get("qualification"),
         data["department_id"], data.get("joining_date"), data.get("status", "active")))

    # Create user account
    if data.get("create_account"):
        # Use provided role_id or fallback to HOD logic
        role_id = data.get("role_id")
        if not role_id:
            role_name = "hod" if data.get("is_hod") else "staff"
            role = query("SELECT role_id FROM role WHERE role_name=%s", (role_name,), fetchone=True)
            if role:
                role_id = role["role_id"]
        
        if role_id:
            execute("""INSERT INTO user_account (username, password_hash, role_id, ref_id, ref_type, is_active)
                       VALUES (%s, %s, %s, %s, 'staff', 1)""",
                    (data["employee_id"], hash_password(data.get("password", data["employee_id"])), role_id, sid))
    log_activity(request.current_user["user_id"], "create", "staff", sid, f"Added staff {data['name']}")
    return success({"staff_id": sid}, "Staff added", 201)

@staff_bp.route("/<int:staff_id>", methods=["PUT"])
@roles_required("super_admin", "admin")
def update_staff(staff_id):
    data = request.get_json()
    execute("""UPDATE staff SET name=%s, email=%s, phone=%s, designation=%s,
               qualification=%s, department_id=%s, status=%s WHERE staff_id=%s""",
            (data["name"], data.get("email"), data.get("phone"), data["designation"],
             data.get("qualification"), data["department_id"], data.get("status", "active"), staff_id))
    log_activity(request.current_user["user_id"], "update", "staff", staff_id, f"Updated staff {data['name']}")
    return success(message="Staff updated")

@staff_bp.route("/<int:staff_id>", methods=["DELETE"])
@roles_required("super_admin", "admin")
def delete_staff(staff_id):
    execute("UPDATE staff SET status='inactive' WHERE staff_id=%s", (staff_id,))
    log_activity(request.current_user["user_id"], "delete", "staff", staff_id, "Deactivated staff")
    return success(message="Staff deactivated")

# --- Subject Allocations ---
@staff_bp.route("/allocations", methods=["GET"])
@login_required
def get_allocations():
    staff_id = request.args.get("staff_id")
    section_id = request.args.get("section_id")
    ay_id = request.args.get("academic_year_id")
    sql = """SELECT sa.*, s.name as staff_name, sub.name as subject_name,
             sec.name as section_name, ay.year_label
             FROM subject_allocation sa
             JOIN staff s ON sa.staff_id=s.staff_id
             JOIN subject sub ON sa.subject_id=sub.subject_id
             JOIN section sec ON sa.section_id=sec.section_id
             JOIN academic_year ay ON sa.academic_year_id=ay.academic_year_id WHERE 1=1"""
    params = []
    if staff_id:
        sql += " AND sa.staff_id=%s"; params.append(staff_id)
    if section_id:
        sql += " AND sa.section_id=%s"; params.append(section_id)
    if ay_id:
        sql += " AND sa.academic_year_id=%s"; params.append(ay_id)
    return success(query(sql, params))

@staff_bp.route("/allocations", methods=["POST"])
@roles_required("super_admin", "admin", "hod")
def add_allocation():
    data = request.get_json()
    aid = execute("""INSERT INTO subject_allocation (staff_id, subject_id, section_id, academic_year_id)
                     VALUES (%s,%s,%s,%s)""",
                  (data["staff_id"], data["subject_id"], data["section_id"], data["academic_year_id"]))
    return success({"allocation_id": aid}, "Allocation created", 201)

@staff_bp.route("/allocations/<int:alloc_id>", methods=["DELETE"])
@roles_required("super_admin", "admin", "hod")
def delete_allocation(alloc_id):
    execute("DELETE FROM subject_allocation WHERE allocation_id=%s", (alloc_id,))
    return success(message="Allocation removed")
