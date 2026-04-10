import os, csv, io
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl

# ----- Phase 2 Helpers -----

def _clean_old_reports():
    """Delete reports older than 30 days."""
    now = datetime.now()
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        return
    for f in os.listdir(REPORTS_DIR):
        fp = os.path.join(REPORTS_DIR, f)
        if os.path.isfile(fp):
            stat = os.stat(fp)
            c_time = datetime.fromtimestamp(stat.st_mtime)
            if now - c_time > timedelta(days=30):
                os.remove(fp)

def _make_pdf(report_type: str, data: list, filename: str):
    filepath = os.path.join(REPORTS_DIR, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title = f"{report_type.upper()} REPORT"
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    if not data:
        elements.append(Paragraph("No data found.", styles['Normal']))
        doc.build(elements)
        return filepath

    # Extract headers
    headers = list(data[0].keys())
    table_data = [headers]
    for row in data:
        table_data.append([str(row.get(h, "")) for h in headers])
        
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(t)
    doc.build(elements)
    return filepath

def _make_excel(report_type: str, data: list, filename: str):
    filepath = os.path.join(REPORTS_DIR, filename)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = report_type.title()

    if not data:
        ws.append(["No data found"])
        wb.save(filepath)
        return filepath

    headers = list(data[0].keys())
    ws.append(headers)
    for row in data:
        ws.append([str(row.get(h, "")) for h in headers])

    wb.save(filepath)
    return filepath

def _execute_generate_report(tool_args: dict, user: dict):
    rt = tool_args.get("report_type", "general")
    fmt = tool_args.get("format", "pdf").lower()
    _clean_old_reports()

    # Query data based on rt
    data = []
    if rt == "students" or rt == "cgpa":
        data = query("SELECT s.name, s.reg_number, d.name as dept, COALESCE(sr.cgpa, 0) as cgpa FROM student s LEFT JOIN course c ON s.course_id=c.course_id LEFT JOIN department d ON c.department_id=d.department_id LEFT JOIN semester_result sr ON sr.student_id=s.student_id WHERE s.status='active' ORDER BY cgpa DESC LIMIT 200")
    elif rt == "fees" or rt == "defaulter":
        data = query("SELECT s.name, s.reg_number, d.name as dept, f.total_fee, COALESCE(f.amount_paid, 0) as paid, (f.total_fee - COALESCE(f.amount_paid, 0)) as pending FROM student s LEFT JOIN fee_payment f ON s.student_id=f.student_id LEFT JOIN course c ON s.course_id=c.course_id LEFT JOIN department d ON c.department_id=d.department_id WHERE s.status='active' AND (f.total_fee - COALESCE(f.amount_paid, 0)) > 0 ORDER BY pending DESC LIMIT 200")
    elif rt == "attendance":
        data = query("SELECT s.name, s.reg_number, ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as pct FROM student s JOIN attendance a ON s.student_id=a.student_id GROUP BY s.student_id HAVING pct < 75 ORDER BY pct ASC")
    elif rt == "department":
        data = query("SELECT d.name, COUNT(s.student_id) as students FROM department d LEFT JOIN course c ON d.department_id=c.department_id LEFT JOIN student s ON c.course_id=s.course_id WHERE s.status='active' GROUP BY d.department_id")
    elif rt == "scholarship":
        data = query("SELECT s.name, s.reg_number, sch.scholarship_type, sch.status FROM scholarship sch JOIN student s ON sch.student_id=s.student_id ORDER BY s.name")
    elif rt == "eligibility":
        data = query("SELECT s.name, s.reg_number, c.criteria_name FROM eligibility_criteria c CROSS JOIN student s ORDER BY s.name LIMIT 100")
    elif rt == "marks":
        data = query("SELECT s.name, s.reg_number, m.marks_obtained, m.total_marks FROM marks m JOIN student s ON m.student_id=s.student_id ORDER BY s.name LIMIT 100")
    else:
        return {"response_type": "text", "message": f"Report type {rt} is not supported directly yet."}

    if not data:
        data = [{"Msg": "No records found matching the report criteria."}]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    fname = f"{rt}_report_{timestamp}.{fmt}"
    
    try:
        if fmt == "excel":
            _make_excel(rt, data, fname)
        else:
            _make_pdf(rt, data, fname)
            
        return {
            "response_type": "report",
            "filename": fname,
            "format": fmt.upper(),
            "download_url": f"/api/aira/reports/{fname}?download=1",
            "preview_url": f"/api/aira/reports/{fname}",
            "message": f"✅ Here is the generated {rt} report."
        }
    except Exception as e:
        return {"response_type": "text", "message": f"Failed to generate {fmt} report: {str(e)}"}

def _execute_navigate_to(tool_args: dict):
    page = tool_args.get("page", "").lower()
    url_map = {
        "dashboard": "/dashboard.html",
        "student": "/students/index.html",
        "staff": "/staff/index.html",
        "department": "/departments/index.html",
        "course": "/courses/index.html",
        "timetable": "/timetable/index.html",
        "attendance": "/attendance/index.html",
        "mark": "/marks/index.html",
        "fee": "/fees/index.html",
        "report": "/reports/index.html",
        "notification": "/notifications/index.html",
        "setting": "/settings/index.html"
    }
    
    target_url = "/dashboard.html"
    target_label = "Dashboard"
    for key, path in url_map.items():
        if key in page:
            target_url = path
            target_label = key.title() + "s" if key != "dashboard" and key != "timetable" else key.title()
            break
            
    return {
        "response_type": "navigate",
        "url": target_url,
        "label": target_label,
        "message": f"I can take you to the {target_label} page."
    }

def _execute_bulk_update_attendance(tool_args: dict):
    subject = tool_args.get("subject_name", "class")
    status = tool_args.get("status", "P")
    date = tool_args.get("date", datetime.now().strftime("%Y-%m-%d"))

    # Need confirmation first
    students = query("SELECT student_id, name, reg_number FROM student WHERE status='active' LIMIT 50")
    
    action_desc = f"Mark ALL visible students as {status} for {subject} on {date}"
    
    return {
        "response_type": "bulk_confirm",
        "action_id": f"bulk_att_{status}_{datetime.now().timestamp()}",
        "action_description": action_desc,
        "count": len(students),
        "students": [{"name": s["name"], "reg_no": s["reg_number"]} for s in students],
        "message": "Please confirm this bulk attendance update."
    }

def _execute_parse_csv_marks(tool_args: dict, user: dict):
    return {"response_type": "text", "message": "CSV parsing is not fully mocked in this snippet."}
