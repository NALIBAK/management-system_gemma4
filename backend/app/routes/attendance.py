from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required
from app.utils.response import success, error
from app.utils.activity import log_activity

attendance_bp = Blueprint("attendance", __name__)

@attendance_bp.route("/", methods=["GET"])
@login_required
def get_attendance():
    section_id = request.args.get("section_id")
    student_id = request.args.get("student_id")
    subject_id = request.args.get("subject_id")
    date = request.args.get("date")
    sql = """SELECT a.*, st.name as student_name, st.roll_number,
             sub.name as subject_name, p.period_number
             FROM attendance a
             JOIN student st ON a.student_id=st.student_id
             JOIN subject sub ON a.subject_id=sub.subject_id
             LEFT JOIN period_definition p ON a.period_id=p.period_id WHERE 1=1"""
    params = []
    if section_id:
        sql += " AND a.section_id=%s"; params.append(section_id)
    if student_id:
        sql += " AND a.student_id=%s"; params.append(student_id)
    if subject_id:
        sql += " AND a.subject_id=%s"; params.append(subject_id)
    if date:
        sql += " AND a.attendance_date=%s"; params.append(date)
    sql += " ORDER BY a.attendance_date DESC, p.period_number"
    return success(query(sql, params))

@attendance_bp.route("/", methods=["POST"])
@roles_required("super_admin", "admin", "hod", "staff")
def save_attendance():
    """Bulk save attendance. Expects {section_id, subject_id, period_id, academic_year_id, date, records: [{student_id, status, remarks}]}"""
    data = request.get_json()
    records = data.get("records", [])
    if not records:
        return error("No attendance records provided")
    for r in records:
        existing = query("""SELECT attendance_id FROM attendance
                            WHERE student_id=%s AND subject_id=%s AND period_id=%s AND attendance_date=%s""",
                         (r["student_id"], data["subject_id"], data["period_id"], data["date"]), fetchone=True)
        if existing:
            execute("UPDATE attendance SET status=%s, remarks=%s WHERE attendance_id=%s",
                    (r.get("status", "P"), r.get("remarks"), existing["attendance_id"]))
        else:
            execute("""INSERT INTO attendance (student_id, subject_id, section_id, period_id, academic_year_id, attendance_date, status, remarks)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (r["student_id"], data["subject_id"], data["section_id"],
                     data["period_id"], data["academic_year_id"], data["date"],
                     r.get("status", "P"), r.get("remarks")))
    log_activity(request.current_user["user_id"], "create", "attendance", None, f"Attendance for {len(records)} students, section {data['section_id']}")
    return success(message=f"Attendance saved for {len(records)} students")

@attendance_bp.route("/summary", methods=["GET"])
@login_required
def get_attendance_summary():
    """Get attendance percentage per student per subject."""
    section_id = request.args.get("section_id")
    student_id = request.args.get("student_id")
    if not section_id and not student_id:
        return error("section_id or student_id required")
    sql = """SELECT a.student_id, st.name as student_name, st.roll_number,
             a.subject_id, sub.name as subject_name,
             COUNT(*) as total_classes,
             SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END) as present_count,
             ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as percentage
             FROM attendance a
             JOIN student st ON a.student_id=st.student_id
             JOIN subject sub ON a.subject_id=sub.subject_id WHERE 1=1"""
    params = []
    if section_id:
        sql += " AND a.section_id=%s"; params.append(section_id)
    if student_id:
        sql += " AND a.student_id=%s"; params.append(student_id)
    sql += " GROUP BY a.student_id, a.subject_id ORDER BY st.roll_number, sub.name"
    return success(query(sql, params))
