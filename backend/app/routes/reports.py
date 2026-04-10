from flask import Blueprint, request, send_file
from app.db import query
from app.utils.auth import login_required, roles_required
from app.utils.response import success, error
import io

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/attendance", methods=["GET"])
@login_required
def attendance_report():
    section_id = request.args.get("section_id")
    subject_id = request.args.get("subject_id")
    threshold = float(request.args.get("threshold", 75))
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
    if subject_id:
        sql += " AND a.subject_id=%s"; params.append(subject_id)
    sql += " GROUP BY a.student_id, a.subject_id HAVING percentage < %s ORDER BY percentage ASC"
    params.append(threshold)
    return success(query(sql, params))

@reports_bp.route("/marks", methods=["GET"])
@login_required
def marks_report():
    section_id = request.args.get("section_id")
    semester_id = request.args.get("semester_id")
    sql = """SELECT sr.*, st.name as student_name, st.reg_number, st.roll_number,
             sem.semester_number, ay.year_label
             FROM semester_result sr
             JOIN student st ON sr.student_id=st.student_id
             JOIN semester sem ON sr.semester_id=sem.semester_id
             JOIN academic_year ay ON sr.academic_year_id=ay.academic_year_id WHERE 1=1"""
    params = []
    if section_id:
        sql += """ AND sr.student_id IN (SELECT student_id FROM student WHERE section_id=%s)"""
        params.append(section_id)
    if semester_id:
        sql += " AND sr.semester_id=%s"; params.append(semester_id)
    sql += " ORDER BY st.roll_number"
    return success(query(sql, params))

@reports_bp.route("/fee-defaulters", methods=["GET"])
@login_required
def fee_defaulters():
    ay_id = request.args.get("academic_year_id")
    dept_id = request.args.get("department_id")
    sql = """SELECT st.student_id, st.name, st.reg_number, st.roll_number,
             COALESCE(SUM(fs.total_amount), 0) as total_due,
             COALESCE(SUM(fp.amount_paid), 0) as total_paid,
             COALESCE(SUM(fs.total_amount), 0) - COALESCE(SUM(fp.amount_paid), 0) as balance
             FROM student st
             JOIN course c ON st.course_id=c.course_id
             LEFT JOIN fee_structure fs ON fs.course_id=c.course_id AND fs.academic_year_id=%s
             LEFT JOIN fee_payment fp ON fp.student_id=st.student_id AND fp.academic_year_id=%s
             WHERE st.status='active'"""
    params = [ay_id, ay_id]
    if dept_id:
        sql += " AND c.department_id=%s"; params.append(dept_id)
    sql += " GROUP BY st.student_id HAVING balance > 0 ORDER BY balance DESC"
    return success(query(sql, params))

@reports_bp.route("/department-summary", methods=["GET"])
@login_required
def department_summary():
    user = request.current_user
    role = user.get("role", "")
    ref_id = user.get("ref_id")  # staff_id for staff/hod roles

    params = []
    dept_filter = ""

    # Scope to staff's own department for non-admin roles
    if role in ("staff", "hod") and ref_id:
        dept_filter = " WHERE d.department_id = (SELECT department_id FROM staff WHERE staff_id = %s)"
        params.append(ref_id)

    sql = f"""SELECT d.department_id, d.name as department_name,
             COUNT(DISTINCT st.student_id) as total_students,
             COUNT(DISTINCT s.staff_id) as total_staff,
             COUNT(DISTINCT c.course_id) as total_courses
             FROM department d
             LEFT JOIN course c ON c.department_id=d.department_id
             LEFT JOIN student st ON st.course_id=c.course_id AND st.status='active'
             LEFT JOIN staff s ON s.department_id=d.department_id AND s.status='active'
             {dept_filter}
             GROUP BY d.department_id ORDER BY d.name"""
    return success(query(sql, params))


# ===== NEW REPORT ENDPOINTS =====

@reports_bp.route("/student-profile", methods=["GET"])
@login_required
def student_profile_report():
    """Student name, reg_no, 8-semester CGPA report."""
    student_id = request.args.get("student_id")
    section_id = request.args.get("section_id")
    department_id = request.args.get("department_id")
    sql = """SELECT st.student_id, st.name, st.reg_number, st.roll_number,
             st.student_category, st.caste_community, st.status,
             c.name as course_name, d.name as department_name, sec.name as section_name,
             COALESCE(sr.cgpa, 0) as cgpa,
             MAX(sem.semester_number) as latest_semester
             FROM student st
             JOIN course c ON st.course_id=c.course_id
             JOIN department d ON c.department_id=d.department_id
             JOIN section sec ON st.section_id=sec.section_id
             LEFT JOIN semester_result sr ON sr.student_id=st.student_id
             LEFT JOIN semester sem ON sr.semester_id=sem.semester_id
             WHERE st.status='active'"""
    params = []
    if student_id:
        sql += " AND st.student_id=%s"; params.append(student_id)
    if section_id:
        sql += " AND st.section_id=%s"; params.append(section_id)
    if department_id:
        sql += " AND c.department_id=%s"; params.append(department_id)
    sql += " GROUP BY st.student_id ORDER BY st.name"
    return success(query(sql, params))


@reports_bp.route("/fee-structure", methods=["GET"])
@login_required
def fee_structure_report():
    """Fee structure breakdown by course, category, semester."""
    course_id = request.args.get("course_id")
    academic_year_id = request.args.get("academic_year_id")
    fee_category_id = request.args.get("fee_category_id")
    sql = """SELECT fs.fee_structure_id, c.name as course_name, fc.name as fee_category,
             fs.semester_number, fs.total_amount, ay.year_label,
             GROUP_CONCAT(CONCAT(fcomp.name, ': ', fsd.amount) SEPARATOR ', ') as components
             FROM fee_structure fs
             JOIN course c ON fs.course_id=c.course_id
             JOIN fee_category fc ON fs.fee_category_id=fc.fee_category_id
             JOIN academic_year ay ON fs.academic_year_id=ay.academic_year_id
             LEFT JOIN fee_structure_detail fsd ON fsd.fee_structure_id=fs.fee_structure_id
             LEFT JOIN fee_component fcomp ON fsd.component_id=fcomp.component_id
             WHERE 1=1"""
    params = []
    if course_id:
        sql += " AND fs.course_id=%s"; params.append(course_id)
    if academic_year_id:
        sql += " AND fs.academic_year_id=%s"; params.append(academic_year_id)
    if fee_category_id:
        sql += " AND fs.fee_category_id=%s"; params.append(fee_category_id)
    sql += " GROUP BY fs.fee_structure_id ORDER BY c.name, fs.semester_number"
    return success(query(sql, params))


@reports_bp.route("/eligibility", methods=["GET"])
@login_required
def eligibility_report():
    """Eligibility criteria report with match/unmatch per student."""
    student_id = request.args.get("student_id")
    section_id = request.args.get("section_id")
    criteria_id = request.args.get("criteria_id")
    sql = """SELECT st.name as student_name, st.reg_number, st.roll_number,
             ec.name as criteria_name, ec.criteria_type, ec.threshold_value, ec.comparison,
             se.status as eligibility_status, se.evaluated_value, se.remarks
             FROM student_eligibility se
             JOIN student st ON se.student_id=st.student_id
             JOIN eligibility_criteria ec ON se.criteria_id=ec.criteria_id
             WHERE st.status='active'"""
    params = []
    if student_id:
        sql += " AND se.student_id=%s"; params.append(student_id)
    if section_id:
        sql += " AND st.section_id=%s"; params.append(section_id)
    if criteria_id:
        sql += " AND se.criteria_id=%s"; params.append(criteria_id)
    sql += " ORDER BY st.name, ec.name"
    return success(query(sql, params))


@reports_bp.route("/category-wise", methods=["GET"])
@login_required
def category_wise_report():
    """Category-wise student report (centac/management/regular)."""
    department_id = request.args.get("department_id")
    course_id = request.args.get("course_id")
    batch_id = request.args.get("batch_id")
    sql = """SELECT st.student_category, c.name as course_name, d.name as department_name,
             COUNT(*) as student_count,
             GROUP_CONCAT(st.name ORDER BY st.name SEPARATOR ', ') as student_names
             FROM student st
             JOIN course c ON st.course_id=c.course_id
             JOIN department d ON c.department_id=d.department_id
             WHERE st.status='active'"""
    params = []
    if department_id:
        sql += " AND c.department_id=%s"; params.append(department_id)
    if course_id:
        sql += " AND st.course_id=%s"; params.append(course_id)
    if batch_id:
        sql += " AND st.batch_id=%s"; params.append(batch_id)
    sql += " GROUP BY st.student_category, c.course_id ORDER BY d.name, c.name, st.student_category"
    return success(query(sql, params))


@reports_bp.route("/scholarship", methods=["GET"])
@login_required
def scholarship_report():
    """Caste/community-wise scholarship report."""
    department_id = request.args.get("department_id")
    academic_year_id = request.args.get("academic_year_id")
    caste_community = request.args.get("caste_community")
    sql = """SELECT st.caste_community, st.name as student_name, st.reg_number,
             c.name as course_name, d.name as department_name,
             sch.scholarship_name, sch.amount, sch.status as scholarship_status,
             ay.year_label
             FROM scholarship sch
             JOIN student st ON sch.student_id=st.student_id
             JOIN course c ON st.course_id=c.course_id
             JOIN department d ON c.department_id=d.department_id
             JOIN academic_year ay ON sch.academic_year_id=ay.academic_year_id
             WHERE 1=1"""
    params = []
    if department_id:
        sql += " AND c.department_id=%s"; params.append(department_id)
    if academic_year_id:
        sql += " AND sch.academic_year_id=%s"; params.append(academic_year_id)
    if caste_community:
        sql += " AND st.caste_community=%s"; params.append(caste_community)
    sql += " ORDER BY st.caste_community, st.name"
    return success(query(sql, params))


@reports_bp.route("/extracurricular", methods=["GET"])
@login_required
def extracurricular_report():
    """Extracurricular activity report — technical & non-technical."""
    student_id = request.args.get("student_id")
    section_id = request.args.get("section_id")
    department_id = request.args.get("department_id")
    activity_type = request.args.get("activity_type")
    sql = """SELECT ea.activity_id, st.name as student_name, st.reg_number, st.roll_number,
             ea.title, ea.activity_type, ea.category, ea.event_date,
             ea.description, ea.achievement,
             c.name as course_name, d.name as department_name
             FROM extracurricular_activity ea
             JOIN student st ON ea.student_id=st.student_id
             JOIN course c ON st.course_id=c.course_id
             JOIN department d ON c.department_id=d.department_id
             WHERE st.status='active'"""
    params = []
    if student_id:
        sql += " AND ea.student_id=%s"; params.append(student_id)
    if section_id:
        sql += " AND st.section_id=%s"; params.append(section_id)
    if department_id:
        sql += " AND c.department_id=%s"; params.append(department_id)
    if activity_type:
        sql += " AND ea.activity_type=%s"; params.append(activity_type)
    sql += " ORDER BY ea.event_date DESC, st.name"
    return success(query(sql, params))


@reports_bp.route("/attendance-detailed", methods=["GET"])
@login_required
def attendance_detailed_report():
    """Flexible attendance report: filter by class, student, dept, subject, date range."""
    section_id = request.args.get("section_id")
    student_id = request.args.get("student_id")
    department_id = request.args.get("department_id")
    subject_id = request.args.get("subject_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    sql = """SELECT a.student_id, st.name as student_name, st.reg_number, st.roll_number,
             sub.name as subject_name, d.name as department_name, sec.name as section_name,
             COUNT(*) as total_classes,
             SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END) as present_count,
             SUM(CASE WHEN a.status='A' THEN 1 ELSE 0 END) as absent_count,
             SUM(CASE WHEN a.status='OD' THEN 1 ELSE 0 END) as od_count,
             ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as percentage
             FROM attendance a
             JOIN student st ON a.student_id=st.student_id
             JOIN subject sub ON a.subject_id=sub.subject_id
             JOIN section sec ON a.section_id=sec.section_id
             JOIN course c ON st.course_id=c.course_id
             JOIN department d ON c.department_id=d.department_id
             WHERE 1=1"""
    params = []
    if section_id:
        sql += " AND a.section_id=%s"; params.append(section_id)
    if student_id:
        sql += " AND a.student_id=%s"; params.append(student_id)
    if department_id:
        sql += " AND c.department_id=%s"; params.append(department_id)
    if subject_id:
        sql += " AND a.subject_id=%s"; params.append(subject_id)
    if date_from:
        sql += " AND a.attendance_date >= %s"; params.append(date_from)
    if date_to:
        sql += " AND a.attendance_date <= %s"; params.append(date_to)
    sql += " GROUP BY a.student_id, a.subject_id ORDER BY d.name, st.name, sub.name"
    return success(query(sql, params))


@reports_bp.route("/marks-detailed", methods=["GET"])
@login_required
def marks_detailed_report():
    """Flexible marks report: filter by class, student, dept, subject, exam type."""
    section_id = request.args.get("section_id")
    student_id = request.args.get("student_id")
    department_id = request.args.get("department_id")
    subject_id = request.args.get("subject_id")
    exam_type_id = request.args.get("exam_type_id")
    sql = """SELECT m.mark_id, st.name as student_name, st.reg_number, st.roll_number,
             e.exam_name, et.name as exam_type, sub.name as subject_name,
             d.name as department_name, sec.name as section_name,
             m.marks_obtained, e.max_marks, e.passing_marks,
             m.is_absent, m.remarks,
             CASE WHEN m.is_absent=1 THEN 'absent'
                  WHEN m.marks_obtained >= e.passing_marks THEN 'pass' ELSE 'fail' END as result_status
             FROM mark m
             JOIN exam e ON m.exam_id=e.exam_id
             JOIN exam_type et ON e.exam_type_id=et.exam_type_id
             JOIN subject sub ON e.subject_id=sub.subject_id
             JOIN section sec ON e.section_id=sec.section_id
             JOIN student st ON m.student_id=st.student_id
             JOIN course c ON st.course_id=c.course_id
             JOIN department d ON c.department_id=d.department_id
             WHERE 1=1"""
    params = []
    if section_id:
        sql += " AND e.section_id=%s"; params.append(section_id)
    if student_id:
        sql += " AND m.student_id=%s"; params.append(student_id)
    if department_id:
        sql += " AND c.department_id=%s"; params.append(department_id)
    if subject_id:
        sql += " AND e.subject_id=%s"; params.append(subject_id)
    if exam_type_id:
        sql += " AND e.exam_type_id=%s"; params.append(exam_type_id)
    sql += " ORDER BY d.name, st.name, sub.name, e.exam_name"
    return success(query(sql, params))
