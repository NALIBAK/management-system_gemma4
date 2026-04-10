from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required
from app.utils.response import success, error
from app.utils.activity import log_activity

marks_bp = Blueprint("marks", __name__)

@marks_bp.route("/exam-types", methods=["GET"])
@login_required
def get_exam_types():
    return success(query("SELECT * FROM exam_type"))

@marks_bp.route("/exams", methods=["GET"])
@login_required
def get_exams():
    section_id = request.args.get("section_id")
    subject_id = request.args.get("subject_id")
    semester_id = request.args.get("semester_id")
    sql = """SELECT e.*, et.name as exam_type_name, sub.name as subject_name
             FROM exam e JOIN exam_type et ON e.exam_type_id=et.exam_type_id
             JOIN subject sub ON e.subject_id=sub.subject_id WHERE 1=1"""
    params = []
    if section_id:
        sql += " AND e.section_id=%s"; params.append(section_id)
    if subject_id:
        sql += " AND e.subject_id=%s"; params.append(subject_id)
    if semester_id:
        sql += " AND e.semester_id=%s"; params.append(semester_id)
    return success(query(sql, params))

@marks_bp.route("/exams", methods=["POST"])
@roles_required("super_admin", "admin", "hod", "staff")
def add_exam():
    data = request.get_json()
    eid = execute("""INSERT INTO exam (exam_type_id, subject_id, section_id, academic_year_id, semester_id,
                     exam_name, exam_date, max_marks, passing_marks, weightage_percent)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                  (data["exam_type_id"], data["subject_id"], data["section_id"],
                   data["academic_year_id"], data["semester_id"], data["exam_name"],
                   data.get("exam_date"), data["max_marks"], data.get("passing_marks", 0),
                   data.get("weightage_percent", 100)))
    log_activity(request.current_user["user_id"], "create", "exam", eid, f"Created exam {data['exam_name']}")
    return success({"exam_id": eid}, "Exam created", 201)

@marks_bp.route("/marks", methods=["GET"])
@login_required
def get_marks():
    exam_id = request.args.get("exam_id")
    student_id = request.args.get("student_id")
    if not exam_id and not student_id:
        return error("exam_id or student_id required")
    sql = """SELECT m.*, st.name as student_name, st.roll_number FROM mark m
             JOIN student st ON m.student_id=st.student_id WHERE 1=1"""
    params = []
    if exam_id:
        sql += " AND m.exam_id=%s"; params.append(exam_id)
    if student_id:
        sql += " AND m.student_id=%s"; params.append(student_id)
    return success(query(sql, params))

@marks_bp.route("/marks", methods=["POST"])
@roles_required("super_admin", "admin", "hod", "staff")
def save_marks():
    """Bulk save marks for an exam. Expects list of {student_id, marks_obtained, is_absent, remarks}"""
    data = request.get_json()
    exam_id = data.get("exam_id")
    marks_list = data.get("marks", [])
    if not exam_id or not marks_list:
        return error("exam_id and marks list required")
    for m in marks_list:
        existing = query("SELECT mark_id FROM mark WHERE exam_id=%s AND student_id=%s",
                         (exam_id, m["student_id"]), fetchone=True)
        if existing:
            execute("UPDATE mark SET marks_obtained=%s, is_absent=%s, remarks=%s WHERE mark_id=%s",
                    (m.get("marks_obtained", 0), m.get("is_absent", False), m.get("remarks"), existing["mark_id"]))
        else:
            execute("INSERT INTO mark (exam_id, student_id, marks_obtained, is_absent, remarks) VALUES (%s,%s,%s,%s,%s)",
                    (exam_id, m["student_id"], m.get("marks_obtained", 0), m.get("is_absent", False), m.get("remarks")))
    log_activity(request.current_user["user_id"], "create", "mark", None, f"Marks saved for {len(marks_list)} students, exam {exam_id}")
    return success(message=f"Marks saved for {len(marks_list)} students")

@marks_bp.route("/results", methods=["GET"])
@login_required
def get_results():
    student_id = request.args.get("student_id")
    semester_id = request.args.get("semester_id")
    sql = """SELECT sr.*, sem.semester_number, ay.year_label FROM semester_result sr
             JOIN semester sem ON sr.semester_id=sem.semester_id
             JOIN academic_year ay ON sr.academic_year_id=ay.academic_year_id WHERE 1=1"""
    params = []
    if student_id:
        sql += " AND sr.student_id=%s"; params.append(student_id)
    if semester_id:
        sql += " AND sr.semester_id=%s"; params.append(semester_id)
    return success(query(sql, params))

@marks_bp.route("/grade-mappings", methods=["GET"])
@login_required
def get_grade_mappings():
    return success(query("SELECT * FROM grade_mapping ORDER BY min_percentage DESC"))
