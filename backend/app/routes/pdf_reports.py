"""
pdf_reports.py — Beautiful PDF Report Blueprint
================================================
Generates professional A4 PDF reports using WeasyPrint + Jinja2 templates.
Saves PDFs to reports_archive/ and returns download links.
"""

import os
import uuid
import datetime
from flask import Blueprint, request, send_file, abort
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.db import query
from app.utils.auth import login_required
from app.utils.response import success, error

pdf_report_bp = Blueprint("pdf_reports", __name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
_here           = os.path.dirname(__file__)
TEMPLATES_DIR   = os.path.join(_here, "..", "report_templates")
ARCHIVE_DIR     = os.path.join(_here, "..", "..", "reports_archive")

os.makedirs(ARCHIVE_DIR, exist_ok=True)

# ── Jinja2 environment ─────────────────────────────────────────────────────────
_jinja_env = Environment(
    loader=FileSystemLoader(os.path.abspath(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

# Load the shared CSS once and inline it into every template
def _load_styles():
    css_path = os.path.join(TEMPLATES_DIR, "report_styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

_STYLES = _load_styles()


# ── Helper: get college info ───────────────────────────────────────────────────
def _get_college():
    row = query("SELECT name, address, phone, email FROM college LIMIT 1", fetchone=True)
    return row or {"name": "College Management System", "address": "", "phone": "", "email": ""}


# ── Helper: render HTML to PDF ─────────────────────────────────────────────────
def _render_pdf(template_name: str, context: dict) -> str:
    """Render a Jinja2 template and write it to a PDF in reports_archive/. Returns filename."""
    from xhtml2pdf import pisa
    import io

    context["style_tag"] = f"<style>{_STYLES}</style>"
    context["generated_at"] = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    context["college"] = _get_college()

    tmpl = _jinja_env.get_template(template_name)
    html_str = tmpl.render(**context)

    filename = (
        f"{template_name.replace('.html', '')}_{uuid.uuid4().hex[:8]}"
        f"_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    )
    filepath = os.path.join(ARCHIVE_DIR, filename)

    with open(filepath, "wb") as pdf_file:
        result = pisa.CreatePDF(html_str, dest=pdf_file, encoding="utf-8")

    if result.err:
        raise RuntimeError(f"xhtml2pdf error: {result.err}")

    return filename


# ── Data builders (one per template) ──────────────────────────────────────────

def _build_student_full_profile(student_id: int) -> dict:
    """Collect all data for student_full_profile.html"""
    student = query("""
        SELECT st.student_id, st.name, st.reg_number, st.roll_number, st.email,
               st.phone, st.gender, st.student_category, st.caste_community, st.status,
               c.name as course_name, d.name as department_name, sec.name as section_name
        FROM student st
        JOIN course c ON st.course_id = c.course_id
        JOIN department d ON c.department_id = d.department_id
        JOIN section sec ON st.section_id = sec.section_id
        WHERE st.student_id = %s
    """, (student_id,), fetchone=True)

    if not student:
        return None

    # CGPA per semester
    cgpa_rows = query("""
        SELECT sem.semester_number, sr.gpa, sr.cgpa
        FROM semester_result sr
        JOIN semester sem ON sr.semester_id = sem.semester_id
        WHERE sr.student_id = %s
        ORDER BY sem.semester_number
    """, (student_id,))

    latest_cgpa = float(cgpa_rows[-1]["cgpa"]) if cgpa_rows and cgpa_rows[-1]["cgpa"] else 0.0

    # Attendance per subject
    attendance = query("""
        SELECT sub.name as subject,
               COUNT(*) as total,
               SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END) as present,
               ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) as pct
        FROM attendance a
        JOIN subject sub ON a.subject_id = sub.subject_id
        WHERE a.student_id = %s
        GROUP BY a.subject_id
        ORDER BY sub.name
    """, (student_id,))

    avg_att_row = query("""
        SELECT ROUND(AVG(pct),2) as avg_pct FROM (
          SELECT ROUND(SUM(CASE WHEN status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) as pct
          FROM attendance WHERE student_id = %s GROUP BY subject_id HAVING COUNT(*) > 0
        ) x
    """, (student_id,), fetchone=True)
    avg_pct = float(avg_att_row["avg_pct"]) if avg_att_row and avg_att_row["avg_pct"] else None

    # Extracurricular activities
    activities = query("""
        SELECT title, activity_type, category, event_date, achievement
        FROM extracurricular_activity
        WHERE student_id = %s
        ORDER BY event_date DESC
    """, (student_id,))

    # Fee status (current academic year)
    ay = query("SELECT academic_year_id FROM academic_year WHERE is_current = 1 LIMIT 1", fetchone=True)
    fee_data = None
    if ay:
        ay_id = ay["academic_year_id"]
        due_row  = query("""SELECT COALESCE(SUM(fs.total_amount),0) as d
                             FROM fee_structure fs JOIN student st ON st.course_id=fs.course_id
                             WHERE st.student_id=%s AND fs.academic_year_id=%s""",
                         (student_id, ay_id), fetchone=True)
        paid_row = query("""SELECT COALESCE(SUM(amount_paid),0) as p
                             FROM fee_payment WHERE student_id=%s AND academic_year_id=%s""",
                         (student_id, ay_id), fetchone=True)
        total_due  = float(due_row["d"])  if due_row  else 0.0
        total_paid = float(paid_row["p"]) if paid_row else 0.0
        fee_data = {
            "total_due":  total_due,
            "total_paid": total_paid,
            "balance":    total_due - total_paid,
        }

    return {
        "report_title":    "Student Full Profile Report",
        "student":         student,
        "cgpa_semesters":  cgpa_rows,
        "latest_cgpa":     latest_cgpa,
        "attendance_data": attendance,
        "attendance_pct":  avg_pct,
        "activities":      activities,
        "total_activities": len(activities),
        "fee_data":        fee_data,
    }


def _build_fee_defaulters(academic_year_id: int = None, department_id: int = None) -> dict:
    ay = None
    if academic_year_id:
        ay = query("SELECT year_label FROM academic_year WHERE academic_year_id=%s",
                   (academic_year_id,), fetchone=True)
    else:
        ay = query("SELECT academic_year_id, year_label FROM academic_year WHERE is_current=1 LIMIT 1",
                   fetchone=True)
        if ay:
            academic_year_id = ay["academic_year_id"]

    fee_where = "AND fs.academic_year_id=%s" if academic_year_id else ""
    pay_where  = "AND academic_year_id=%s"   if academic_year_id else ""

    sql = f"""
        SELECT st.name, st.reg_number, st.roll_number,
               c.name as course_name, d.name as department_name,
               COALESCE(fs_total.total_due, 0) as total_due,
               COALESCE(fp_total.total_paid, 0) as total_paid,
               COALESCE(fs_total.total_due, 0) - COALESCE(fp_total.total_paid, 0) as balance
        FROM student st
        JOIN course c ON st.course_id=c.course_id
        JOIN department d ON c.department_id=d.department_id
        LEFT JOIN (
            SELECT st2.student_id, SUM(fs.total_amount) as total_due
            FROM student st2 JOIN fee_structure fs ON fs.course_id=st2.course_id
            WHERE 1=1 {fee_where} GROUP BY st2.student_id
        ) fs_total ON fs_total.student_id=st.student_id
        LEFT JOIN (
            SELECT student_id, SUM(amount_paid) as total_paid
            FROM fee_payment WHERE 1=1 {pay_where} GROUP BY student_id
        ) fp_total ON fp_total.student_id=st.student_id
        WHERE st.status='active'
    """
    params = []
    if academic_year_id:
        params.extend([academic_year_id, academic_year_id])
    if department_id:
        sql += " AND c.department_id=%s"
        params.append(department_id)
    sql += " HAVING balance > 0 ORDER BY balance DESC"

    rows = query(sql, params)
    # Convert Decimal to float for Jinja2
    defaulters = []
    for r in rows:
        defaulters.append({
            **r,
            "total_due":  float(r.get("total_due",  0) or 0),
            "total_paid": float(r.get("total_paid", 0) or 0),
            "balance":    float(r.get("balance",    0) or 0),
        })

    total_outstanding = sum(d["balance"] for d in defaulters)
    avg_balance = total_outstanding / len(defaulters) if defaulters else 0
    dept_set = set(d["department_name"] for d in defaulters)

    return {
        "report_title":      "Fee Defaulters Report",
        "academic_year":     ay["year_label"] if ay else "All Years",
        "defaulters":        defaulters,
        "total_outstanding": total_outstanding,
        "avg_balance":       avg_balance,
        "departments_count": len(dept_set),
    }


def _build_attendance_summary(section_id=None, student_id=None,
                               department_id=None, subject_id=None,
                               date_from=None, date_to=None) -> dict:
    sql = """
        SELECT st.name as student_name, st.reg_number, sub.name as subject_name,
               sec.name as section_name, d.name as department_name,
               COUNT(*) as total_classes,
               SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END) as present,
               ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) as pct
        FROM attendance a
        JOIN student st ON a.student_id=st.student_id
        JOIN subject sub ON a.subject_id=sub.subject_id
        JOIN section sec ON a.section_id=sec.section_id
        JOIN course c ON st.course_id=c.course_id
        JOIN department d ON c.department_id=d.department_id
        WHERE 1=1
    """
    params = []
    filters = []
    if section_id:    sql += " AND a.section_id=%s";    params.append(section_id);    filters.append(f"Section ID {section_id}")
    if student_id:    sql += " AND a.student_id=%s";    params.append(student_id);    filters.append(f"Student ID {student_id}")
    if department_id: sql += " AND c.department_id=%s"; params.append(department_id); filters.append(f"Dept ID {department_id}")
    if subject_id:    sql += " AND a.subject_id=%s";    params.append(subject_id);    filters.append(f"Subject ID {subject_id}")
    if date_from:     sql += " AND a.attendance_date >= %s"; params.append(date_from)
    if date_to:       sql += " AND a.attendance_date <= %s"; params.append(date_to)
    sql += " GROUP BY a.student_id, a.subject_id ORDER BY st.name"

    rows = query(sql, params)
    data = [{**r, "pct": float(r.get("pct") or 0)} for r in rows]

    total  = len(set(r["student_name"] + r["reg_number"] for r in data))
    avg_att = sum(r["pct"] for r in data) / len(data) if data else 0
    b75    = sum(1 for r in data if r["pct"] < 75)
    a90    = sum(1 for r in data if r["pct"] >= 90)

    return {
        "report_title":   "Attendance Summary Report",
        "data":           data,
        "total_students": total,
        "avg_attendance": avg_att,
        "below75_count":  b75,
        "above90_count":  a90,
        "filter_label":   ", ".join(filters) if filters else "All Students",
        "date_from":      date_from,
        "date_to":        date_to,
    }


# ── API Routes ─────────────────────────────────────────────────────────────────

@pdf_report_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    """
    POST /api/pdf-reports/generate
    Body: { "template": "student_full_profile", "params": { "student_id": 42 } }
    Returns: { "download_url": "/api/pdf-reports/download/filename.pdf", "filename": "..." }
    """
    data = request.get_json() or {}
    template = data.get("template", "")
    params   = data.get("params", {})

    try:
        if template == "student_full_profile":
            student_id = params.get("student_id")
            if not student_id:
                return error("student_id is required for student_full_profile report", 400)
            ctx = _build_student_full_profile(int(student_id))
            if not ctx:
                return error(f"No student found with ID {student_id}", 404)
            filename = _render_pdf("student_full_profile.html", ctx)

        elif template == "fee_defaulters":
            ctx = _build_fee_defaulters(
                academic_year_id=params.get("academic_year_id"),
                department_id=params.get("department_id"),
            )
            filename = _render_pdf("fee_defaulters.html", ctx)

        elif template == "attendance_summary":
            ctx = _build_attendance_summary(
                section_id=params.get("section_id"),
                student_id=params.get("student_id"),
                department_id=params.get("department_id"),
                subject_id=params.get("subject_id"),
                date_from=params.get("date_from"),
                date_to=params.get("date_to"),
            )
            filename = _render_pdf("attendance_summary.html", ctx)

        else:
            return error(f"Unknown template: '{template}'. Available: student_full_profile, fee_defaulters, attendance_summary", 400)

    except Exception as e:
        return error(f"PDF generation failed: {str(e)}", 500)

    download_url = f"/api/pdf-reports/download/{filename}"
    return success({
        "download_url": download_url,
        "filename": filename,
        "template": template,
    }, "PDF report generated successfully")


@pdf_report_bp.route("/download/<filename>", methods=["GET"])
@login_required
def download(filename):
    """Serve a generated PDF file."""
    # Safety check — no path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        abort(400)
    filepath = os.path.join(ARCHIVE_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)


@pdf_report_bp.route("/list", methods=["GET"])
@login_required
def list_reports():
    """List all archived PDF reports."""
    files = []
    for fname in sorted(os.listdir(ARCHIVE_DIR), reverse=True):
        if fname.endswith(".pdf"):
            fp = os.path.join(ARCHIVE_DIR, fname)
            files.append({
                "filename": fname,
                "size_kb": round(os.path.getsize(fp) / 1024, 1),
                "created": datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M"),
                "download_url": f"/api/pdf-reports/download/{fname}",
            })
    return success(files)
