from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required
from app.utils.response import success, error
from app.utils.activity import log_activity

fees_bp = Blueprint("fees", __name__)

@fees_bp.route("/categories", methods=["GET"])
@login_required
def get_categories():
    return success(query("SELECT * FROM fee_category"))

@fees_bp.route("/components", methods=["GET"])
@login_required
def get_components():
    return success(query("SELECT * FROM fee_component"))

@fees_bp.route("/structures", methods=["GET"])
@login_required
def get_structures():
    course_id = request.args.get("course_id")
    ay_id = request.args.get("academic_year_id")
    sql = """SELECT fs.*, c.name as course_name, fc.name as category_name, ay.year_label
             FROM fee_structure fs
             JOIN course c ON fs.course_id=c.course_id
             JOIN fee_category fc ON fs.fee_category_id=fc.fee_category_id
             JOIN academic_year ay ON fs.academic_year_id=ay.academic_year_id WHERE 1=1"""
    params = []
    if course_id:
        sql += " AND fs.course_id=%s"; params.append(course_id)
    if ay_id:
        sql += " AND fs.academic_year_id=%s"; params.append(ay_id)
    return success(query(sql, params))

@fees_bp.route("/structures", methods=["POST"])
@roles_required("super_admin", "admin")
def add_structure():
    data = request.get_json()
    fsid = execute("""INSERT INTO fee_structure (course_id, fee_category_id, semester_number, academic_year_id, total_amount)
                      VALUES (%s,%s,%s,%s,%s)""",
                   (data["course_id"], data["fee_category_id"], data["semester_number"],
                    data["academic_year_id"], data["total_amount"]))
    # Add detail breakdown
    for detail in data.get("details", []):
        execute("INSERT INTO fee_structure_detail (fee_structure_id, component_id, amount) VALUES (%s,%s,%s)",
                (fsid, detail["component_id"], detail["amount"]))
    return success({"fee_structure_id": fsid}, "Fee structure created", 201)

@fees_bp.route("/payments", methods=["GET"])
@login_required
def get_payments():
    student_id = request.args.get("student_id")
    ay_id = request.args.get("academic_year_id")
    sql = """SELECT fp.*, st.name as student_name, st.reg_number FROM fee_payment fp
             JOIN student st ON fp.student_id=st.student_id WHERE 1=1"""
    params = []
    if student_id:
        sql += " AND fp.student_id=%s"; params.append(student_id)
    if ay_id:
        sql += " AND fp.academic_year_id=%s"; params.append(ay_id)
    sql += " ORDER BY fp.payment_date DESC"
    return success(query(sql, params))

@fees_bp.route("/payments", methods=["POST"])
@roles_required("super_admin", "admin")
def add_payment():
    data = request.get_json()
    pid = execute("""INSERT INTO fee_payment (student_id, fee_structure_id, academic_year_id,
                     amount_paid, payment_date, payment_mode, receipt_number, transaction_ref, remarks)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                  (data["student_id"], data["fee_structure_id"], data["academic_year_id"],
                   data["amount_paid"], data.get("payment_date"), data["payment_mode"],
                   data.get("receipt_number"), data.get("transaction_ref"), data.get("remarks")))
    log_activity(request.current_user["user_id"], "create", "fee_payment", pid, f"Payment ₹{data['amount_paid']} for student {data['student_id']}")
    return success({"payment_id": pid}, "Payment recorded", 201)

@fees_bp.route("/balance/<int:student_id>", methods=["GET"])
@login_required
def get_balance(student_id):
    ay_id = request.args.get("academic_year_id")
    total_due = query("""SELECT COALESCE(SUM(fs.total_amount), 0) as total_due
                         FROM fee_structure fs
                         JOIN student st ON st.course_id=fs.course_id
                         WHERE st.student_id=%s AND fs.academic_year_id=%s""",
                      (student_id, ay_id), fetchone=True)
    total_paid = query("""SELECT COALESCE(SUM(amount_paid), 0) as total_paid FROM fee_payment
                          WHERE student_id=%s AND academic_year_id=%s""",
                       (student_id, ay_id), fetchone=True)
    scholarships = query("""SELECT COALESCE(SUM(amount), 0) as scholarship_total FROM scholarship
                            WHERE student_id=%s AND academic_year_id=%s AND status='approved'""",
                         (student_id, ay_id), fetchone=True)
    due = float(total_due["total_due"])
    paid = float(total_paid["total_paid"])
    schol = float(scholarships["scholarship_total"])
    return success({
        "total_due": due,
        "total_paid": paid,
        "scholarship": schol,
        "balance": due - paid - schol
    })

@fees_bp.route("/scholarships", methods=["GET"])
@login_required
def get_scholarships():
    student_id = request.args.get("student_id")
    sql = "SELECT * FROM scholarship WHERE 1=1"
    params = []
    if student_id:
        sql += " AND student_id=%s"; params.append(student_id)
    return success(query(sql, params))

@fees_bp.route("/scholarships", methods=["POST"])
@roles_required("super_admin", "admin")
def add_scholarship():
    data = request.get_json()
    sid = execute("""INSERT INTO scholarship (student_id, academic_year_id, scholarship_name, amount, status)
                     VALUES (%s,%s,%s,%s,%s)""",
                  (data["student_id"], data["academic_year_id"], data["scholarship_name"],
                   data["amount"], data.get("status", "pending")))
    log_activity(request.current_user["user_id"], "create", "scholarship", sid, f"Scholarship {data['scholarship_name']} for student {data['student_id']}")
    return success({"scholarship_id": sid}, "Scholarship added", 201)
