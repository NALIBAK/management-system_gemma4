from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required
from app.utils.response import success, error
import requests as http_requests
import json

aira_bp = Blueprint("aira", __name__)

# MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "get_student_info",
        "description": "Retrieve student details by ID, name, or registration number",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Student ID, name, or reg number"}
            },
            "required": ["identifier"]
        }
    },
    {
        "name": "get_attendance_summary",
        "description": "Get attendance percentage for students in a section or for a specific student",
        "inputSchema": {
            "type": "object",
            "properties": {
                "section_id": {"type": "integer"},
                "student_id": {"type": "integer"},
                "threshold": {"type": "number", "description": "Filter students below this percentage"}
            }
        }
    },
    {
        "name": "update_attendance",
        "description": "Update attendance status for a student on a specific date",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "integer"},
                "subject_id": {"type": "integer"},
                "date": {"type": "string", "format": "date"},
                "status": {"type": "string", "enum": ["P", "A", "OD"]}
            },
            "required": ["student_id", "subject_id", "date", "status"]
        }
    },
    {
        "name": "get_marks",
        "description": "Get marks for a student or an exam",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "integer"},
                "exam_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_fee_balance",
        "description": "Get fee balance for a student",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "integer"},
                "academic_year_id": {"type": "integer"}
            },
            "required": ["student_id", "academic_year_id"]
        }
    },
    {
        "name": "get_department_summary",
        "description": "Get summary statistics for all departments",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "generate_student_profile_report",
        "description": "Generate student profile report with name, reg no, CGPA, course, department",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "integer"},
                "section_id": {"type": "integer"},
                "department_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "generate_fee_structure_report",
        "description": "Generate fee structure report showing breakdown by course, category, semester",
        "inputSchema": {
            "type": "object",
            "properties": {
                "course_id": {"type": "integer"},
                "academic_year_id": {"type": "integer"},
                "fee_category_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "generate_eligibility_report",
        "description": "Generate eligibility criteria report showing match/unmatch status per student",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "integer"},
                "section_id": {"type": "integer"},
                "criteria_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "generate_category_wise_report",
        "description": "Generate category-wise student report (centac/management/regular)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "department_id": {"type": "integer"},
                "course_id": {"type": "integer"},
                "batch_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "generate_scholarship_report",
        "description": "Generate caste/community-wise scholarship report",
        "inputSchema": {
            "type": "object",
            "properties": {
                "department_id": {"type": "integer"},
                "academic_year_id": {"type": "integer"},
                "caste_community": {"type": "string"}
            }
        }
    },
    {
        "name": "generate_extracurricular_report",
        "description": "Generate extracurricular activities report (technical and non-technical)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "integer"},
                "section_id": {"type": "integer"},
                "department_id": {"type": "integer"},
                "activity_type": {"type": "string", "enum": ["technical", "non_technical"]}
            }
        }
    },
    {
        "name": "generate_attendance_report",
        "description": "Generate detailed attendance report with flexible filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "section_id": {"type": "integer"},
                "student_id": {"type": "integer"},
                "department_id": {"type": "integer"},
                "subject_id": {"type": "integer"},
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"}
            }
        }
    },
    {
        "name": "generate_marks_report",
        "description": "Generate detailed marks report with flexible filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "section_id": {"type": "integer"},
                "student_id": {"type": "integer"},
                "department_id": {"type": "integer"},
                "subject_id": {"type": "integer"},
                "exam_type_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_top_students",
        "description": "Get top N students by CGPA or attendance percentage",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of top students (default 10)"},
                "department_id": {"type": "integer"},
                "order_by": {"type": "string", "enum": ["cgpa", "attendance"]}
            }
        }
    },
    {
        "name": "get_low_attendance",
        "description": "Get students with attendance percentage below a threshold",
        "inputSchema": {
            "type": "object",
            "properties": {
                "threshold": {"type": "number", "description": "Percentage threshold (default 75)"},
                "section_id": {"type": "integer"},
                "department_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_fee_defaulters",
        "description": "Get students who have pending fee balance (defaulters)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "academic_year_id": {"type": "integer"},
                "department_id": {"type": "integer"},
                "min_balance": {"type": "number", "description": "Minimum balance amount to include"}
            }
        }
    },
    {
        "name": "get_staff_by_department",
        "description": "Get staff list for a department or all departments",
        "inputSchema": {
            "type": "object",
            "properties": {
                "department_id": {"type": "integer"},
                "designation": {"type": "string"}
            }
        }
    },
    {
        "name": "get_student_by_name",
        "description": "Search for a student by name (fuzzy match), returns their full profile",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Student name or partial name"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_sections_list",
        "description": "Get list of all sections with their course and department",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_combined_summary",
        "description": "Get full college dashboard summary: counts, averages, top departments",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_student_profile_detail",
        "description": "Get detailed private profile of a specific student including email and phone number. Use this when the admin needs full contact details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Roll number, Registration number, or Name of the student"}
            },
            "required": ["identifier"]
        }
    },
    {
        "name": "generate_report",
        "description": "Generate a downloadable file report (PDF or Excel) for various types of data. Always use this tool when the user asks to EXPORT, DOWNLOAD, CREATE A FILE, or asks for a 'pdf file'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "description": "The type of report to generate (e.g., students, cgpa, fees). Default to 'students' if referring to a specific student.",
                    "enum": ["students", "cgpa", "fees", "defaulter", "attendance", "department", "scholarship", "eligibility", "marks", "general"]
                },
                "format": {
                    "type": "string",
                    "description": "The file format for the output report (default: pdf)",
                    "enum": ["pdf", "excel"]
                }
            },
            "required": ["report_type"]
        }
    },
    {
        "name": "generate_beautiful_pdf_report",
        "description": "Generate a beautifully formatted, professional A4 PDF report with the college letterhead and institutional styling. Use this for: full student profile (CGPA per semester + attendance + activities + fees), fee defaulters list, or attendance summary. Always prefer this over generate_report when the user asks for a 'beautiful', 'formatted', 'full', 'complete', 'detailed', or 'download' report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template": {
                    "type": "string",
                    "description": "Which report template to use",
                    "enum": ["student_full_profile", "fee_defaulters", "attendance_summary"]
                },
                "student_id":        {"type": "integer", "description": "Student ID (required for student_full_profile)"},
                "section_id":        {"type": "integer", "description": "Section ID filter (for attendance_summary)"},
                "department_id":     {"type": "integer", "description": "Department ID filter"},
                "academic_year_id":  {"type": "integer", "description": "Academic year ID (for fee_defaulters)"},
                "subject_id":        {"type": "integer", "description": "Subject ID filter (for attendance_summary)"},
                "date_from":         {"type": "string",  "description": "Start date YYYY-MM-DD (for attendance_summary)"},
                "date_to":           {"type": "string",  "description": "End date YYYY-MM-DD (for attendance_summary)"}
            },
            "required": ["template"]
        }
    },
    {
        "name": "send_whatsapp_notification",
        "description": "Send a personalized WhatsApp message to an array of phone numbers. Use this to notify parents, students, or staff about important updates like fee defaults, attendance records, or meeting alerts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phone_numbers": {
                    "type": "array",
                    "items": { "type": "string" },
                    "description": "List of phone numbers to send the message to (requires country code, but defaults to +91 if 10 digits)"
                },
                "message": {
                    "type": "string",
                    "description": "The exact text message to send"
                }
            },
            "required": ["phone_numbers", "message"]
        }
    }
]

import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import csv
REPORTS_DIR = 'reports'

def get_user_scope(user: dict) -> dict:
    """"Calculate data access scope based on role."""
    scope = {"role": user["role"], "dept_ids": [], "course_ids": [], "section_ids": []}
    if user["role"] in ["super_admin", "admin"]:
        scope["is_global"] = True
    elif user["role"] == "hod":
        scope["is_global"] = False
        dept = query("SELECT department_id FROM staff WHERE staff_id=%s", (user["ref_id"],), fetchone=True)
        if dept:
            scope["dept_ids"].append(dept["department_id"])
    elif user["role"] == "staff":
        scope["is_global"] = False
        # Get assigned sections
        allocs = query("SELECT DISTINCT section_id FROM subject_allocation WHERE staff_id=%s", (user["ref_id"],))
        scope["section_ids"] = [a["section_id"] for a in allocs]
        # Get implicit departments via those sections
        if scope["section_ids"]:
            placeholders = ",".join(["%s"] * len(scope["section_ids"]))
            depts = query(f"SELECT DISTINCT c.department_id, c.course_id FROM section s JOIN course c ON s.course_id=c.course_id WHERE s.section_id IN ({placeholders})", tuple(scope["section_ids"]))
            scope["dept_ids"] = list(set([d["department_id"] for d in depts]))
            scope["course_ids"] = list(set([d["course_id"] for d in depts]))
    return scope

def execute_tool(tool_name: str, tool_args: dict, user: dict) -> dict:
    """Execute an MCP tool call and return the result."""
    result = None
    scope = get_user_scope(user)
    
    try:
        if tool_name == "generate_beautiful_pdf_report":
            return _execute_beautiful_pdf_report(tool_args, user)
        elif tool_name == "send_whatsapp_notification":
            return _execute_send_whatsapp_notification(tool_args, user)
        elif tool_name == "generate_report":
            return _execute_generate_report(tool_args, user)
        elif tool_name == "navigate_to":
            return _execute_navigate_to(tool_args)
        elif tool_name == "bulk_update_attendance":
            return _execute_bulk_update_attendance(tool_args)
        elif tool_name == "parse_csv_marks":
            return _execute_parse_csv_marks(tool_args, user)

        if tool_name == "get_student_info":
            identifier = tool_args.get("identifier", "")
            result = query("""SELECT st.student_id, st.name, st.reg_number, st.roll_number,
                              st.email as student_email, st.phone as student_phone, st.status,
                              s.name as section_name, c.name as course_name
                              FROM student st JOIN section s ON st.section_id=s.section_id
                              JOIN course c ON st.course_id=c.course_id
                              WHERE st.student_id=%s OR st.reg_number=%s OR st.roll_number LIKE %s OR st.name LIKE %s""",
                           (identifier, identifier, f"%{identifier}%", f"%{identifier}%"))
            return {"success": True, "data": result}

        elif tool_name == "get_attendance_summary":
            sql = """SELECT a.student_id, st.name, st.roll_number, sub.name as subject,
                     COUNT(*) as total, SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END) as present,
                     ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as pct
                     FROM attendance a JOIN student st ON a.student_id=st.student_id
                     JOIN subject sub ON a.subject_id=sub.subject_id WHERE 1=1"""
            params = []
            if tool_args.get("section_id"):
                sql += " AND a.section_id=%s"; params.append(tool_args["section_id"])
            if tool_args.get("student_id"):
                sql += " AND a.student_id=%s"; params.append(tool_args["student_id"])
            sql += " GROUP BY a.student_id, a.subject_id"
            if tool_args.get("threshold"):
                sql += " HAVING pct < %s"; params.append(tool_args["threshold"])
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "get_marks":
            sql = """SELECT m.*, st.name, st.roll_number, e.exam_name, sub.name as subject
                     FROM mark m JOIN student st ON m.student_id=st.student_id
                     JOIN exam e ON m.exam_id=e.exam_id JOIN subject sub ON e.subject_id=sub.subject_id WHERE 1=1"""
            params = []
            if tool_args.get("student_id"):
                sql += " AND m.student_id=%s"; params.append(tool_args["student_id"])
            if tool_args.get("exam_id"):
                sql += " AND m.exam_id=%s"; params.append(tool_args["exam_id"])
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "get_fee_balance":
            from app.routes.fees import get_balance
            # Inline the balance calculation
            student_id = tool_args["student_id"]
            ay_id = tool_args["academic_year_id"]
            total_due = query("SELECT COALESCE(SUM(fs.total_amount),0) as d FROM fee_structure fs JOIN student st ON st.course_id=fs.course_id WHERE st.student_id=%s AND fs.academic_year_id=%s", (student_id, ay_id), fetchone=True)
            total_paid = query("SELECT COALESCE(SUM(amount_paid),0) as p FROM fee_payment WHERE student_id=%s AND academic_year_id=%s", (student_id, ay_id), fetchone=True)
            return {"success": True, "data": {"balance": float(total_due["d"]) - float(total_paid["p"])}}

        elif tool_name == "get_department_summary":
            result = query("""SELECT d.name, COUNT(DISTINCT st.student_id) as students,
                              COUNT(DISTINCT s.staff_id) as staff FROM department d
                              LEFT JOIN course c ON c.department_id=d.department_id
                              LEFT JOIN student st ON st.course_id=c.course_id
                              LEFT JOIN staff s ON s.department_id=d.department_id
                              GROUP BY d.department_id""")
            return {"success": True, "data": result}

        elif tool_name == "generate_student_profile_report":
            sql = """SELECT st.name as student_name, st.reg_number, st.roll_number,
                     st.email as student_email, st.phone as student_phone,
                     c.name as course_name, d.name as department_name,
                     sec.name as section_name, COALESCE(MAX(sr.cgpa), 0) as current_cgpa
                     FROM student st
                     JOIN course c ON st.course_id=c.course_id
                     JOIN department d ON c.department_id=d.department_id
                     JOIN section sec ON st.section_id=sec.section_id
                     LEFT JOIN semester_result sr ON sr.student_id=st.student_id
                     LEFT JOIN semester sem ON sr.semester_id=sem.semester_id
                     WHERE st.status='active'"""
            params = []
            if tool_args.get("student_id"):
                sql += " AND st.student_id=%s"; params.append(tool_args["student_id"])
            if tool_args.get("section_id"):
                sql += " AND st.section_id=%s"; params.append(tool_args["section_id"])
            if tool_args.get("department_id"):
                sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
            sql += " GROUP BY st.student_id ORDER BY d.name, st.reg_number, st.name"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "generate_fee_structure_report":
            sql = """SELECT c.name as course_name, fc.name as fee_category,
                     fs.semester_number, fs.total_amount, ay.year_label
                     FROM fee_structure fs
                     JOIN course c ON fs.course_id=c.course_id
                     JOIN fee_category fc ON fs.fee_category_id=fc.fee_category_id
                     JOIN academic_year ay ON fs.academic_year_id=ay.academic_year_id
                     WHERE 1=1"""
            params = []
            if tool_args.get("course_id"):
                sql += " AND fs.course_id=%s"; params.append(tool_args["course_id"])
            if tool_args.get("academic_year_id"):
                sql += " AND fs.academic_year_id=%s"; params.append(tool_args["academic_year_id"])
            if tool_args.get("fee_category_id"):
                sql += " AND fs.fee_category_id=%s"; params.append(tool_args["fee_category_id"])
            sql += " ORDER BY c.name, fs.semester_number"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "generate_eligibility_report":
            sql = """SELECT st.name as student_name, st.reg_number,
                     ec.name as criteria_name, ec.criteria_type, ec.threshold_value,
                     se.status as eligibility_status, se.evaluated_value, se.remarks
                     FROM student_eligibility se
                     JOIN student st ON se.student_id=st.student_id
                     JOIN eligibility_criteria ec ON se.criteria_id=ec.criteria_id
                     WHERE st.status='active'"""
            params = []
            if tool_args.get("student_id"):
                sql += " AND se.student_id=%s"; params.append(tool_args["student_id"])
            if tool_args.get("section_id"):
                sql += " AND st.section_id=%s"; params.append(tool_args["section_id"])
            if tool_args.get("criteria_id"):
                sql += " AND se.criteria_id=%s"; params.append(tool_args["criteria_id"])
            sql += " ORDER BY d.name, st.reg_number, st.name, ec.name"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "generate_category_wise_report":
            sql = """SELECT st.student_category, c.name as course_name, d.name as department_name,
                     COUNT(*) as student_count
                     FROM student st
                     JOIN course c ON st.course_id=c.course_id
                     JOIN department d ON c.department_id=d.department_id
                     WHERE st.status='active'"""
            params = []
            if tool_args.get("department_id"):
                sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
            if tool_args.get("course_id"):
                sql += " AND st.course_id=%s"; params.append(tool_args["course_id"])
            if tool_args.get("batch_id"):
                sql += " AND st.batch_id=%s"; params.append(tool_args["batch_id"])
            sql += " GROUP BY st.student_category, c.course_id ORDER BY d.name, c.name"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "generate_scholarship_report":
            sql = """SELECT st.caste_community, st.name as student_name, st.reg_number,
                     c.name as course_name, sch.scholarship_name, sch.amount, sch.status as scholarship_status
                     FROM scholarship sch
                     JOIN student st ON sch.student_id=st.student_id
                     JOIN course c ON st.course_id=c.course_id
                     JOIN department d ON c.department_id=d.department_id
                     JOIN academic_year ay ON sch.academic_year_id=ay.academic_year_id
                     WHERE 1=1"""
            params = []
            if tool_args.get("department_id"):
                sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
            if tool_args.get("academic_year_id"):
                sql += " AND sch.academic_year_id=%s"; params.append(tool_args["academic_year_id"])
            if tool_args.get("caste_community"):
                sql += " AND st.caste_community=%s"; params.append(tool_args["caste_community"])
            sql += " ORDER BY d.name, st.reg_number, st.name"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "generate_extracurricular_report":
            sql = """SELECT st.name as student_name, st.reg_number,
                     ea.title, ea.activity_type, ea.category, ea.event_date, ea.achievement,
                     c.name as course_name, d.name as department_name
                     FROM extracurricular_activity ea
                     JOIN student st ON ea.student_id=st.student_id
                     JOIN course c ON st.course_id=c.course_id
                     JOIN department d ON c.department_id=d.department_id
                     WHERE st.status='active'"""
            params = []
            if tool_args.get("student_id"):
                sql += " AND ea.student_id=%s"; params.append(tool_args["student_id"])
            if tool_args.get("section_id"):
                sql += " AND st.section_id=%s"; params.append(tool_args["section_id"])
            if tool_args.get("department_id"):
                sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
            if tool_args.get("activity_type"):
                sql += " AND ea.activity_type=%s"; params.append(tool_args["activity_type"])
            sql += " ORDER BY d.name, st.reg_number, st.name, ea.event_date DESC"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "generate_attendance_report":
            sql = """SELECT st.name as student_name, st.reg_number, sub.name as subject_name,
                     d.name as department_name, sec.name as section_name,
                     COUNT(*) as total_classes,
                     SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END) as present,
                     ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as pct
                     FROM attendance a
                     JOIN student st ON a.student_id=st.student_id
                     JOIN subject sub ON a.subject_id=sub.subject_id
                     JOIN section sec ON a.section_id=sec.section_id
                     JOIN course c ON st.course_id=c.course_id
                     JOIN department d ON c.department_id=d.department_id
                     WHERE 1=1"""
            params = []
            if tool_args.get("section_id"):
                sql += " AND a.section_id=%s"; params.append(tool_args["section_id"])
            if tool_args.get("student_id"):
                sql += " AND a.student_id=%s"; params.append(tool_args["student_id"])
            if tool_args.get("department_id"):
                sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
            if tool_args.get("subject_id"):
                sql += " AND a.subject_id=%s"; params.append(tool_args["subject_id"])
            if tool_args.get("date_from"):
                sql += " AND a.attendance_date >= %s"; params.append(tool_args["date_from"])
            if tool_args.get("date_to"):
                sql += " AND a.attendance_date <= %s"; params.append(tool_args["date_to"])
            sql += " GROUP BY a.student_id, a.subject_id ORDER BY d.name, st.reg_number, st.name"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "generate_marks_report":
            sql = """SELECT st.name as student_name, st.reg_number,
                     e.exam_name, et.name as exam_type, sub.name as subject_name,
                     d.name as department_name, sec.name as section_name,
                     m.marks_obtained, e.max_marks, e.passing_marks,
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
            if tool_args.get("section_id"):
                sql += " AND e.section_id=%s"; params.append(tool_args["section_id"])
            if tool_args.get("student_id"):
                sql += " AND m.student_id=%s"; params.append(tool_args["student_id"])
            if tool_args.get("department_id"):
                sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
            if tool_args.get("subject_id"):
                sql += " AND e.subject_id=%s"; params.append(tool_args["subject_id"])
            if tool_args.get("exam_type_id"):
                sql += " AND e.exam_type_id=%s"; params.append(tool_args["exam_type_id"])
            sql += " ORDER BY d.name, st.reg_number, st.name, sub.name"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "update_attendance":
            # Write operation — requires confirmation, do NOT execute directly
            student_id = tool_args.get("student_id")
            subject_id = tool_args.get("subject_id")
            date = tool_args.get("date")
            att_status = tool_args.get("status", "P")
            # Look up names for the preview
            student = query("SELECT name, reg_number FROM student WHERE student_id=%s", (student_id,), fetchone=True)
            subject = query("SELECT name FROM subject WHERE subject_id=%s", (subject_id,), fetchone=True)
            student_name = student["name"] if student else f"ID:{student_id}"
            subject_name = subject["name"] if subject else f"ID:{subject_id}"
            status_label = {"P": "Present", "A": "Absent", "OD": "On Duty"}.get(att_status, att_status)
            # Store as pending action
            action_id = execute(
                """INSERT INTO aira_action_log
                   (user_id, action_type, entity_type, action_details, status)
                   VALUES (%s, 'write', 'attendance', %s, 'pending')""",
                (user["user_id"], json.dumps(tool_args))
            )
            return {
                "success": True,
                "needs_confirmation": True,
                "action_id": action_id,
                "preview": f"Mark **{student_name}** as **{status_label}** for **{subject_name}** on **{date}**"
            }

        elif tool_name == "get_top_students":
            limit = int(tool_args.get("limit", 10))
            order_by = tool_args.get("order_by", "cgpa")
            if order_by == "attendance":
                sql = """SELECT st.name, st.reg_number, st.roll_number,
                         c.name as course_name, d.name as department_name,
                         ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as attendance_pct
                         FROM student st
                         JOIN course c ON st.course_id=c.course_id
                         JOIN department d ON c.department_id=d.department_id
                         JOIN attendance a ON a.student_id=st.student_id
                         WHERE st.status='active'"""
                params = []
                if tool_args.get("department_id"):
                    sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
                sql += f" GROUP BY st.student_id ORDER BY attendance_pct DESC LIMIT {limit}"
            else:
                sql = """SELECT st.name, st.reg_number, c.name as course_name,
                         d.name as department_name, COALESCE(MAX(sr.cgpa),0) as cgpa
                         FROM student st
                         JOIN course c ON st.course_id=c.course_id
                         JOIN department d ON c.department_id=d.department_id
                         LEFT JOIN semester_result sr ON sr.student_id=st.student_id
                         WHERE st.status='active'"""
                params = []
                if tool_args.get("department_id"):
                    sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
                sql += f" GROUP BY st.student_id ORDER BY cgpa DESC LIMIT {limit}"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "get_low_attendance":
            threshold = float(tool_args.get("threshold", 75))
            sql = """SELECT st.name, st.reg_number, st.roll_number,
                     c.name as course_name, d.name as department_name,
                     sec.name as section_name,
                     COUNT(*) as total_classes,
                     SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END) as present,
                     ROUND(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as attendance_pct
                     FROM attendance a
                     JOIN student st ON a.student_id=st.student_id
                     JOIN course c ON st.course_id=c.course_id
                     JOIN department d ON c.department_id=d.department_id
                     JOIN section sec ON st.section_id=sec.section_id
                     WHERE st.status='active'"""
            params = []
            if tool_args.get("section_id"):
                sql += " AND a.section_id=%s"; params.append(tool_args["section_id"])
            if tool_args.get("department_id"):
                sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
            sql += " GROUP BY a.student_id HAVING attendance_pct < %s ORDER BY attendance_pct ASC"
            params.append(threshold)
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "get_fee_defaulters":
            min_balance = float(tool_args.get("min_balance", 0))
            ay_id = tool_args.get("academic_year_id")
            fee_where = "AND fs.academic_year_id=%s" if ay_id else ""
            pay_where = "AND academic_year_id=%s" if ay_id else ""
            sql = f"""SELECT st.name, st.reg_number, st.roll_number,
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
                     WHERE st.status='active'"""
            params = []
            if ay_id:
                params.extend([ay_id, ay_id])
            if tool_args.get("department_id"):
                sql += " AND c.department_id=%s"; params.append(tool_args["department_id"])
            sql += " HAVING balance > %s ORDER BY balance DESC"
            params.append(min_balance)
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "get_staff_by_department":
            sql = """SELECT s.name, s.designation, s.email, s.phone,
                     d.name as department_name, d.code as dept_code,
                     s.qualification, s.experience_years
                     FROM staff s
                     LEFT JOIN department d ON s.department_id=d.department_id
                     WHERE s.status='active'"""
            params = []
            if tool_args.get("department_id"):
                sql += " AND s.department_id=%s"; params.append(tool_args["department_id"])
            if tool_args.get("designation"):
                sql += " AND s.designation LIKE %s"; params.append(f"%{tool_args['designation']}%")
            sql += " ORDER BY d.name, s.name"
            return {"success": True, "data": query(sql, params)}

        elif tool_name == "get_student_by_name":
            name = tool_args.get("name", "")
            result = query("""SELECT st.student_id, st.name, st.reg_number, st.roll_number,
                              st.email, st.phone, st.gender, st.student_category,
                              st.caste_community, st.status,
                              c.name as course_name, d.name as department_name,
                              sec.name as section_name,
                              COALESCE(MAX(sr.cgpa), 0) as cgpa
                              FROM student st
                              JOIN course c ON st.course_id=c.course_id
                              JOIN department d ON c.department_id=d.department_id
                              JOIN section sec ON st.section_id=sec.section_id
                              LEFT JOIN semester_result sr ON sr.student_id=st.student_id
                              WHERE (st.name LIKE %s OR st.reg_number LIKE %s) AND st.status='active'
                              GROUP BY st.student_id ORDER BY st.name""",
                           (f"%{name}%", f"%{name}%"))
            return {"success": True, "data": result}

        elif tool_name == "get_sections_list":
            result = query("""SELECT sec.section_id, sec.name as section_name,
                              c.name as course_name, d.name as department_name,
                              COALESCE(sem.semester_number, 0) as semester_number,
                              COUNT(st.student_id) as student_count
                              FROM section sec
                              JOIN course c ON sec.course_id=c.course_id
                              JOIN department d ON c.department_id=d.department_id
                              LEFT JOIN semester sem ON sec.semester_id=sem.semester_id
                              LEFT JOIN student st ON st.section_id=sec.section_id AND st.status='active'
                              GROUP BY sec.section_id ORDER BY d.name, c.name, semester_number""")
            return {"success": True, "data": result}

        elif tool_name == "get_combined_summary":
            students = query("SELECT COUNT(*) as c FROM student WHERE status='active'", fetchone=True)
            staff    = query("SELECT COUNT(*) as c FROM staff WHERE status='active'", fetchone=True)
            courses  = query("SELECT COUNT(*) as c FROM course", fetchone=True)
            depts    = query("SELECT COUNT(*) as c FROM department", fetchone=True)
            subjects = query("SELECT COUNT(*) as c FROM subject", fetchone=True)
            fees     = query("SELECT COALESCE(SUM(amount_paid),0) as total FROM fee_payment", fetchone=True)
            att_avg  = query("""SELECT ROUND(AVG(pct),2) as avg FROM (
                SELECT ROUND(SUM(CASE WHEN status='P' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as pct
                FROM attendance GROUP BY student_id,subject_id HAVING COUNT(*)>0) x""", fetchone=True)
            dept_stats = query("""SELECT d.name, COUNT(DISTINCT st.student_id) as students,
                                  COUNT(DISTINCT s.staff_id) as staff
                                  FROM department d
                                  LEFT JOIN course c ON c.department_id=d.department_id
                                  LEFT JOIN student st ON st.course_id=c.course_id AND st.status='active'
                                  LEFT JOIN staff s ON s.department_id=d.department_id AND s.status='active'
                                  GROUP BY d.department_id ORDER BY students DESC""")
            return {"success": True, "data": {
                "summary": {
                    "active_students": students["c"] if students else 0,
                    "active_staff": staff["c"] if staff else 0,
                    "courses": courses["c"] if courses else 0,
                    "departments": depts["c"] if depts else 0,
                    "subjects": subjects["c"] if subjects else 0,
                    "total_fees_collected": float(fees["total"]) if fees else 0,
                    "avg_attendance_pct": float(att_avg["avg"]) if att_avg and att_avg["avg"] else 0,
                },
                "departments": dept_stats
            }}

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # Log every tool execution to aira_action_log
        if result is not None:
            try:
                execute(
                    """INSERT INTO aira_action_log (user_id, action_type, entity_type, action_details, status)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (user["user_id"], "tool_call", tool_name,
                     json.dumps({"args": tool_args}),
                     "success" if result.get("success") else "error")
                )
            except Exception:
                pass

def _get_db_context(user: dict) -> str:
    """Query the database for a real-time snapshot to inject into the AIRA system prompt."""
    try:
        scope = get_user_scope(user)
        
        dept_cond = ""
        course_cond = ""
        sec_cond_st = ""
        staff_cond = ""
        staff_cond_join = ""
        
        if not scope.get("is_global"):
            if scope["dept_ids"]:
                d_ins = ",".join(map(str, scope["dept_ids"]))
                dept_cond = f"WHERE department_id IN ({d_ins})"
                course_cond = f"WHERE department_id IN ({d_ins})"
                staff_cond = f"WHERE status='active' AND department_id IN ({d_ins})"
                staff_cond_join = f"WHERE s.status='active' AND s.department_id IN ({d_ins})"
            else:
                dept_cond = "WHERE 1=0"
                course_cond = "WHERE 1=0"
                staff_cond = "WHERE 1=0"
                staff_cond_join = "WHERE 1=0"
                
            if scope["role"] == "staff":
                if scope["section_ids"]:
                    s_ins = ",".join(map(str, scope["section_ids"]))
                    sec_cond_st = f"WHERE status='active' AND section_id IN ({s_ins})"
                else:
                    sec_cond_st = "WHERE 1=0"
            elif scope["dept_ids"]:
                # HOD
                c_ins = ",".join(map(str, scope["course_ids"] if scope.get("course_ids") else [0])) # HOD might not have course_ids populated this way, wait let's use a subquery
                sec_cond_st = f"WHERE status='active' AND course_id IN (SELECT course_id FROM course WHERE department_id IN ({','.join(map(str, scope['dept_ids']))}))"
            else:
                sec_cond_st = "WHERE 1=0"
        else:
            staff_cond = "WHERE status='active'"
            staff_cond_join = "WHERE s.status='active'"
            sec_cond_st = "WHERE status='active'"

        students = query(f"SELECT COUNT(*) as c FROM student {sec_cond_st}", fetchone=True)
        staff    = query(f"SELECT COUNT(*) as c FROM staff {staff_cond}", fetchone=True)
        courses  = query(f"SELECT COUNT(*) as c FROM course {course_cond}", fetchone=True)
        depts    = query(f"SELECT COUNT(*) as c FROM department {dept_cond}", fetchone=True)

        dept_list  = query(f"SELECT name, code FROM department {dept_cond} ORDER BY name")
        course_list = query(f"SELECT name, code, degree_type FROM course {course_cond} ORDER BY name")
        staff_list  = query(f"SELECT s.name, s.designation, d.name as dept FROM staff s LEFT JOIN department d ON s.department_id=d.department_id {staff_cond_join} ORDER BY s.name")
        student_list = query(f"SELECT name, reg_number, roll_number FROM student {sec_cond_st} ORDER BY name")

        ctx = f"""
=== LIVE DATABASE SNAPSHOT ({user['role'].upper()} VIEW) ===

COUNTS:
- Accessible Students: {students['c']}
- Accessible Staff: {staff['c']}
- Accessible Departments: {depts['c']}

DEPARTMENTS:
""" + "\n".join(f"  • {d['name']} [{d['code']}]" for d in dept_list) + """

COURSES:
""" + "\n".join(f"  • {c['name']} ({c['code']}) — {c['degree_type']}" for c in course_list) + """

STAFF:
""" + "\n".join(f"  • {s['name']} — {s['designation']} ({s['dept'] or 'N/A'})" for s in staff_list[:50]) + """

STUDENTS (Sample limit 50):
""" + "\n".join(f"  • {s['name']} (Reg: {s['reg_number']})" for s in student_list[:50]) + f"""

=== END OF DATABASE SNAPSHOT ===
IMPORTANT INSTRUCTIONS FOR AI:
1. Answer ONLY from the data above or the database tools provided.
2. The user is a '{user['role']}'. You must strictly respect their data scope. Do not try to guess data they cannot see.
3. PDF/FILE GENERATION: If the user asks for a "pdf", "excel", "download", or "report" (e.g., "i need it as a pdf file"), you MUST call the `generate_report` tool.
"""
        return ctx
    except Exception as e:
        return f"\n[DB context unavailable: {str(e)}]\n"

def _get_category_context() -> str:
    """Get student category and caste/community distribution for context."""
    try:
        cat_dist = query("""SELECT student_category, COUNT(*) as cnt
                            FROM student WHERE status='active'
                            GROUP BY student_category""")
        caste_dist = query("""SELECT COALESCE(caste_community, 'Not Set') as community, COUNT(*) as cnt
                              FROM student WHERE status='active'
                              GROUP BY caste_community""")
        activities = query("""SELECT activity_type, COUNT(*) as cnt
                              FROM extracurricular_activity ea
                              JOIN student st ON ea.student_id=st.student_id
                              WHERE st.status='active'
                              GROUP BY activity_type""")
        criteria = query("SELECT name, criteria_type, threshold_value, comparison FROM eligibility_criteria WHERE is_active=1")
        ctx = ""
        if cat_dist:
            ctx += "  Admission Categories: " + ", ".join(f"{c['student_category']}: {c['cnt']}" for c in cat_dist) + "\n"
        if caste_dist:
            ctx += "  Caste/Community: " + ", ".join(f"{c['community']}: {c['cnt']}" for c in caste_dist) + "\n"
        if activities:
            ctx += "  Extracurricular: " + ", ".join(f"{a['activity_type']}: {a['cnt']}" for a in activities) + "\n"
        if criteria:
            ctx += "  Eligibility Criteria: " + ", ".join(f"{c['name']} ({c['criteria_type']} {c['comparison']} {c['threshold_value']})" for c in criteria) + "\n"
        return ctx if ctx else "  No category data available yet.\n"
    except:
        return "  Category data unavailable.\n"

from aira.router import route_query


@aira_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()
    message = data.get("message", "")
    conversation_id = data.get("conversation_id")
    page_context = data.get("page_context", "")
    user = request.current_user

    if not message:
        return error("Message is required")

    # Lazy cleanup: delete expired conversations
    try:
        execute("DELETE FROM aira_message WHERE conversation_id IN (SELECT conversation_id FROM aira_conversation WHERE expires_at < NOW())")
        execute("DELETE FROM aira_conversation WHERE expires_at < NOW()")
    except Exception:
        pass

    # Get or create conversation
    if not conversation_id:
        from datetime import datetime, timedelta
        expires = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        conversation_id = execute("""INSERT INTO aira_conversation (user_id, title, page_context, expires_at)
                                     VALUES (%s,%s,%s,%s)""",
                                  (user["user_id"], message[:50], page_context, expires))

    # Save user message
    execute("INSERT INTO aira_message (conversation_id, role, content) VALUES (%s,'user',%s)",
            (conversation_id, message))

    # Get conversation history
    history_records = query("SELECT role, content FROM aira_message WHERE conversation_id=%s ORDER BY created_at",
                    (conversation_id,))
    history = [{"role": h["role"], "content": h["content"]} for h in history_records]

    # Get Scope from Database Role
    scope = get_user_scope(user)

    # Route Request using the specialized AIRA Router
    try:
        route_response = route_query(message, user, history, page_context, scope)
        
        # Determine if it's an interactive widget (Report, Navigate, Bulk Action)
        if isinstance(route_response, dict) and route_response.get("response_type"):
            return success({
                "conversation_id": conversation_id,
                "response": route_response.get("message", ""),
                "needs_confirmation": route_response.get("response_type") == "bulk_confirm",
                **route_response  # Inject full dictionary params like filename, action_id
            })
            
        final_answer = route_response.get("response", "I could not generate a response.")
        tool_calls_made = route_response.get("tool_calls", [])
        
    except Exception as e:
        final_answer = f"⚠️ Sorry, I encountered an error while processing your query: {str(e)}"
        tool_calls_made = []

    # Save assistant response
    execute("INSERT INTO aira_message (conversation_id, role, content) VALUES (%s,'assistant',%s)",
            (conversation_id, final_answer))

    return success({
        "conversation_id": conversation_id,
        "response": final_answer,
        "tool_calls": tool_calls_made
    })




def _smart_fallback(message: str, user: dict, messages: list = None) -> str:
    """Rule-based smart fallback that queries the DB to answer common questions."""
    msg = message.lower().strip()
    
    try:
        # Student queries
        if any(k in msg for k in ["how many student", "student count", "total student", "number of student"]):
            result = query("SELECT COUNT(*) as count FROM student WHERE status='active'", fetchone=True)
            count = result["count"] if result else 0
            return f"📊 There are currently **{count} active students** enrolled in the college."

        # Check for specific student profile queries by Roll No or Reg No
        import re as _re
        id_match = _re.search(r'(?:roll no|reg no|student)\s+([A-Z0-9]{5,20})', msg, _re.IGNORECASE)
        if id_match:
            sid = id_match.group(1).upper()
            result = execute_tool("get_student_info", {"identifier": sid}, user)
            if result.get("success") and result.get("data"):
                st = result["data"][0]
                return f"""🎓 **Student Profile Found:**\n\n**Name:** {st['name']}\n**Roll No:** {st['roll_number']}\n**Reg No:** {st['reg_number']}\n**Course:** {st['course_name']}\n**Section:** {st['section_name']}\n**Email:** {st['student_email']}\n**Phone:** {st['student_phone']}\n**Status:** {st['status'].upper()}"""
            
        # Check if message is really a report query (avoid false-matching "show student CGPA report" as "show student")
        report_keywords = ["cgpa", "profile report", "category", "eligibility", "scholarship", "extracurricular",
                           "extra curricular", "fee structure", "fee breakdown", "fee report",
                           "attendance report", "attendance for", "attendance of",
                           "marks report", "mark report", "marks for", "marks of"]
        is_report_query = any(k in msg for k in report_keywords)

        if not is_report_query and any(k in msg for k in ["list student", "all student", "show student"]):
            students = query("SELECT name, reg_number, status FROM student ORDER BY name LIMIT 10")
            if not students:
                return "No students found in the database yet."
            lines = [f"• {s['name']} ({s['reg_number']}) — {s['status']}" for s in students]
            return f"📋 **Students** (showing up to 10):\n" + "\n".join(lines)

        # Department queries
        if any(k in msg for k in ["how many department", "department count", "total department"]):
            result = query("SELECT COUNT(*) as count FROM department", fetchone=True)
            return f"🏫 There are **{result['count']} departments** in the college."

        if any(k in msg for k in ["list department", "all department", "show department"]):
            depts = query("SELECT name, code FROM department ORDER BY name")
            if not depts:
                return "No departments found."
            lines = [f"• {d['name']} ({d['code']})" for d in depts]
            return "🏫 **Departments:**\n" + "\n".join(lines)

        # Staff queries
        if any(k in msg for k in ["how many staff", "staff count", "total staff", "how many teacher", "how many faculty"]):
            result = query("SELECT COUNT(*) as count FROM staff WHERE status='active'", fetchone=True)
            return f"👨‍🏫 There are **{result['count']} active staff members** in the college."

        if any(k in msg for k in ["list staff", "all staff", "show staff"]):
            staff = query("SELECT name, designation FROM staff WHERE status='active' ORDER BY name LIMIT 10")
            if not staff:
                return "No staff found."
            lines = [f"• {s['name']} — {s['designation']}" for s in staff]
            return "👨‍🏫 **Staff Members:**\n" + "\n".join(lines)

        # Course queries
        if any(k in msg for k in ["how many course", "course count", "total course"]):
            result = query("SELECT COUNT(*) as count FROM course", fetchone=True)
            return f"📚 There are **{result['count']} courses** offered by the college."

        if any(k in msg for k in ["list course", "all course", "show course"]):
            courses = query("SELECT name, code, degree_type FROM course ORDER BY name")
            if not courses:
                return "No courses found."
            lines = [f"• {c['name']} ({c['code']}) — {c['degree_type']}" for c in courses]
            return "📚 **Courses:**\n" + "\n".join(lines)

        # Subject queries
        if any(k in msg for k in ["how many subject", "subject count", "total subject"]):
            result = query("SELECT COUNT(*) as count FROM subject", fetchone=True)
            return f"📖 There are **{result['count']} subjects** in the curriculum."

        # Attendance queries
        if "attendance" in msg and any(k in msg for k in ["average", "overall", "summary", "how is"]):
            result = query("""SELECT ROUND(AVG(pct), 2) as avg_attendance FROM (
                SELECT ROUND(SUM(CASE WHEN status='P' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct
                FROM attendance GROUP BY student_id, subject_id
            ) as sub""", fetchone=True)
            avg = result["avg_attendance"] if result and result["avg_attendance"] else "N/A"
            return f"📅 The **overall average attendance** across all students is **{avg}%**."

        # Fee queries
        if any(k in msg for k in ["total fee", "fee collected", "fee payment"]):
            result = query("SELECT COALESCE(SUM(amount_paid), 0) as total FROM fee_payment", fetchone=True)
            total = float(result["total"]) if result else 0
            return f"💰 Total fees collected so far: **₹{total:,.2f}**"

        # Department summary
        if "department summary" in msg or "dept summary" in msg:
            result = execute_tool("get_department_summary", {}, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{d['name']}**: {d['students']} students, {d['staff']} staff" for d in result["data"]]
                return "🏫 **Department Summary:**\n" + "\n".join(lines)

        # ===== NEW REPORT SMART FALLBACKS =====

        # --- Department-specific student report (e.g. "all IT department students with email as pdf") ---
        import re as _re2
        dept_kw = any(k in msg for k in ["department student", "students in", "students of", "all students",
                                          "report of all", "students with mail", "students with email",
                                          "students with phone", "contact detail"])
        if dept_kw or ("department" in msg and ("student" in msg or "pdf" in msg or "excel" in msg or "report" in msg)):
            # Try to find a department name in the message
            all_depts = query("SELECT department_id, name, code FROM department")
            dept_id, dept_label = None, None
            if all_depts:
                for d in all_depts:
                    if d["name"].lower() in msg or d["code"].lower() in msg:
                        dept_id = d["department_id"]
                        dept_label = d["name"]
                        break
                # Also try common short-forms ("IT", "CSE", "ECE", "EEE", "MECH" etc.)
                if not dept_id:
                    for d in all_depts:
                        short = d["code"].lower()
                        if short in msg.split():
                            dept_id = d["department_id"]
                            dept_label = d["name"]
                            break
            # Query students, optionally filtered by department
            args = {"department_id": dept_id} if dept_id else {}
            fmt = "excel" if "excel" in msg else "pdf"
            is_file_req = any(k in msg for k in ["pdf", "excel", "download", "report", "file", "export"])
            if is_file_req:
                # Generate filtered PDF/Excel via existing tool pipeline
                res = execute_tool("generate_report", {"report_type": "cgpa", "format": fmt, **args}, user)
                label = f"{dept_label} " if dept_label else ""
                if res.get("response_type") == "report":
                    return f"✅ **{label}Student Report Generated**\n\nClick here to download: [{res['filename']}]({res['download_url']})"
                return "❌ Failed to generate the department student report."
            else:
                # Just show in chat
                sql = """SELECT st.name as student_name, st.reg_number, st.roll_number,
                         st.email as student_email, st.phone as student_phone,
                         c.name as course_name, d.name as department_name,
                         sec.name as section_name
                         FROM student st
                         JOIN course c ON st.course_id=c.course_id
                         JOIN department d ON c.department_id=d.department_id
                         JOIN section sec ON st.section_id=sec.section_id
                         WHERE st.status='active'"""
                params = []
                if dept_id:
                    sql += " AND d.department_id=%s"; params.append(dept_id)
                sql += " ORDER BY st.name LIMIT 50"
                students = query(sql, params)
                label = dept_label if dept_label else "All"
                if not students: return f"📊 No active students found for {label} department."
                lines = [f"• **{s['student_name']}** | Roll: {s['roll_number']} | Email: {s['student_email']} | Phone: {s['student_phone']}" for s in students]
                return f"📊 **{label} Department Students** ({len(lines)} shown):\n" + "\n".join(lines[:20]) + (f"\n...and {len(lines)-20} more. Ask for a PDF export to see all." if len(lines) > 20 else "")

        # Check if user explicitly wants to download/export a report file
        is_export = any(k in msg for k in ["download", "export", "generate file", "create pdf", "create excel", "save report", "as a pdf", "pdf file", "in pdf", "pdf format", "excel file", "in excel"])
        
        # Also treat it as an export if the user just says "pdf", "excel", "download it"
        if not is_export and (msg == "pdf" or msg == "excel" or msg == "download" or "need pdf" in msg or "want pdf" in msg or "need it as a pdf" in msg):
            is_export = True

        if is_export:
            fmt = "excel" if "excel" in msg else "pdf"
            rt = None
            if any(k in msg for k in ["cgpa", "profile", "student"]): rt = "cgpa"
            elif any(k in msg for k in ["fee structure", "fee breakdown", "fees"]): rt = "fees"
            elif any(k in msg for k in ["defaulter", "pending fee", "unpaid fee"]): rt = "defaulter"
            elif "attendance" in msg: rt = "attendance"
            elif "department" in msg: rt = "department"
            elif "scholarship" in msg or "caste" in msg or "community" in msg: rt = "scholarship"
            elif "eligibility" in msg: rt = "eligibility"
            elif "marks" in msg: rt = "marks"
            elif "category" in msg or "centac" in msg or "management" in msg: rt = "category"
            elif "extracurricular" in msg or "extra curricular" in msg or "activit" in msg: rt = "extracurricular"
            
            # Contextual Inference: If the user didn't specify the report type in this message,
            # glance at the last message the assistant sent to infer the context.
            if not rt and messages:
                last_bot_msg = next((m["content"].lower() for m in reversed(messages) if m["role"] == "model" or m["role"] == "assistant"), "")
                if "student profile found" in last_bot_msg or "cgpa report" in last_bot_msg: rt = "cgpa"
                elif "fee structure" in last_bot_msg: rt = "fees"
                elif "defaulter" in last_bot_msg or "pending fee" in last_bot_msg: rt = "defaulter"
                elif "attendance" in last_bot_msg: rt = "attendance"
                elif "department" in last_bot_msg: rt = "department"
                elif "scholarship" in last_bot_msg: rt = "scholarship"
                elif "eligibility" in last_bot_msg: rt = "eligibility"
                elif "marks" in last_bot_msg: rt = "marks"
                elif "category-wise" in last_bot_msg or "admission categories" in last_bot_msg: rt = "category"
                elif "extracurricular" in last_bot_msg: rt = "extracurricular"
                else: rt = "general" # fallback
            elif not rt:
                rt = "general"
                
            if rt:
                res = execute_tool("generate_report", {"report_type": rt, "format": fmt}, user)
                if res.get("response_type") == "report":
                    return f"✅ **Report Generated Successfully**\n\nClick here to download: [{res['filename']}]({res['download_url']})"
                return "❌ Failed to generate report file."

        # CGPA / Student Profile Report
        if any(k in msg for k in ["cgpa report", "student profile report", "profile report", "cgpa of"]):
            result = execute_tool("generate_student_profile_report", {}, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{s.get('student_name', s.get('name', 'Unknown'))}** (Reg: {s['reg_number']}) — CGPA: **{s.get('current_cgpa', s.get('cgpa', 0))}**, Course: {s['course_name']}, Dept: {s['department_name']}" for s in result["data"]]
                return f"📊 **Student Profile / CGPA Report** ({len(result['data'])} students):\n" + "\n".join(lines)
            return "📊 No student profile data available yet."

        # Fee Structure Report
        if any(k in msg for k in ["fee structure", "fee breakdown", "fee report"]):
            result = execute_tool("generate_fee_structure_report", {}, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{f['course_name']}** — {f['fee_category']} — Sem {f['semester_number']}: ₹{float(f['total_amount']):,.0f}" for f in result["data"]]
                return f"💰 **Fee Structure Report** ({len(result['data'])} entries):\n" + "\n".join(lines)
            return "💰 No fee structure data available yet. Fee structures need to be configured in the Fees module."

        # Eligibility Report
        if any(k in msg for k in ["eligibility report", "eligible student", "eligibility criteria"]):
            result = execute_tool("generate_eligibility_report", {}, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{e['student_name']}** ({e['reg_number']}) — {e['criteria_name']}: **{e['eligibility_status'].upper()}** (Value: {e.get('evaluated_value', 'N/A')}, Threshold: {e['threshold_value']})" for e in result["data"]]
                return f"🎯 **Eligibility Report** ({len(result['data'])} evaluations):\n" + "\n".join(lines)
            return "🎯 No eligibility evaluations found yet. Use the Eligibility module to evaluate students against criteria."

        # Category-wise Report
        if any(k in msg for k in ["category wise", "category report", "centac student", "management student"]):
            result = execute_tool("generate_category_wise_report", {}, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{c.get('student_category', 'regular').upper()}** — {c['course_name']} ({c['department_name']}): **{c['student_count']} students**" for c in result["data"]]
                return f"🏷️ **Category-wise Student Report**:\n" + "\n".join(lines)
            return "🏷️ No category data available. Update student records with admission category (centac/management)."

        # Scholarship Report
        if any(k in msg for k in ["scholarship report", "caste wise", "community wise", "sc/st", "obc scholarship"]):
            result = execute_tool("generate_scholarship_report", {}, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{s['student_name']}** ({s.get('caste_community', 'N/A')}) — {s['scholarship_name']}: ₹{float(s['amount']):,.0f} [{s['scholarship_status']}]" for s in result["data"]]
                return f"🎓 **Scholarship Report** ({len(result['data'])} scholarships):\n" + "\n".join(lines)
            return "🎓 No scholarship data available yet. Add scholarships in the Fees module."

        # Extracurricular Report
        if any(k in msg for k in ["extracurricular", "extra curricular", "technical activit", "non technical activit"]):
            args = {}
            if "technical" in msg and "non" not in msg:
                args["activity_type"] = "technical"
            elif "non technical" in msg or "non-technical" in msg:
                args["activity_type"] = "non_technical"
            result = execute_tool("generate_extracurricular_report", args, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{a['student_name']}** — {a['title']} ({a['activity_type']}/{a.get('category', 'N/A')}) — {a.get('achievement', 'N/A')}" for a in result["data"]]
                return f"🏆 **Extracurricular Activities Report** ({len(result['data'])} activities):\n" + "\n".join(lines)
            return "🏆 No extracurricular activities recorded yet."

        # Attendance Report (extended)
        if any(k in msg for k in ["attendance report", "attendance of", "attendance for"]):
            result = execute_tool("generate_attendance_report", {}, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{a['student_name']}** ({a['reg_number']}) — {a['subject_name']}: {a['present']}/{a['total_classes']} (**{a['pct']}%**)" for a in result["data"]]
                return f"📅 **Attendance Report** ({len(result['data'])} records):\n" + "\n".join(lines[:20])
            return "📅 No attendance records found."

        # Marks Report (extended)
        if any(k in msg for k in ["marks report", "mark report", "marks of", "marks for"]):
            result = execute_tool("generate_marks_report", {}, user)
            if result.get("success") and result.get("data"):
                lines = [f"• **{m['student_name']}** — {m['subject_name']} ({m['exam_name']}): {m['marks_obtained']}/{m['max_marks']} [{m['result_status']}]" for m in result["data"]]
                return f"📝 **Marks Report** ({len(result['data'])} records):\n" + "\n".join(lines[:20])
            return "📝 No marks records found."

        # ===== NEW AUTONOMOUS TOOL SMART FALLBACKS =====

        # Top students
        import re as _re
        top_match = _re.search(r'top\s+(\d+)', msg)
        top_n = int(top_match.group(1)) if top_match else 10
        if any(k in msg for k in ["top student", "best student", "highest cgpa", "top 5", "top 10"]):
            order = "attendance" if "attendance" in msg else "cgpa"
            result = execute_tool("get_top_students", {"limit": top_n, "order_by": order}, user)
            if result.get("success") and result.get("data"):
                rows = result["data"]
                col = "attendance_pct" if order == "attendance" else "cgpa"
                col_label = "Attendance %" if order == "attendance" else "CGPA"
                header = f"| # | Name | Reg No | Course | {col_label} |\n|---|---|---|---|---|\n"
                table = "".join(f"| {i+1} | **{r['name']}** | {r['reg_number']} | {r['course_name']} | **{r.get(col, 0)}** |\n" for i, r in enumerate(rows))
                return f"🏆 **Top {len(rows)} Students by {col_label}:**\n\n{header}{table}"
            return "🏆 No student data available yet."

        # Low attendance
        thr_match = _re.search(r'below\s+(\d+)', msg)
        threshold = float(thr_match.group(1)) if thr_match else 75.0
        if any(k in msg for k in ["low attendance", "below 75", "below attendance", "attendance defaulter"]):
            result = execute_tool("get_low_attendance", {"threshold": threshold}, user)
            if result.get("success") and result.get("data"):
                rows = result["data"]
                header = "| Name | Reg No | Section | Present | Total | Attendance % |\n|---|---|---|---|---|---|\n"
                table = "".join(f"| **{r['name']}** | {r['reg_number']} | {r.get('section_name','N/A')} | {r['present']} | {r['total_classes']} | **{r['attendance_pct']}%** |\n" for r in rows)
                return f"⚠️ **Students with Attendance Below {threshold}%** ({len(rows)} students):\n\n{header}{table}" if rows else f"✅ No students found with attendance below {threshold}%."
            return "⚠️ No attendance data available yet."

        # Fee defaulters
        if any(k in msg for k in ["defaulter", "fee defaulter", "pending fee", "unpaid fee", "fee balance", "fee due"]):
            result = execute_tool("get_fee_defaulters", {}, user)
            if result.get("success") and result.get("data"):
                rows = result["data"]
                header = "| Name | Reg No | Course | Total Due | Paid | Balance |\n|---|---|---|---|---|---|\n"
                table = "".join(f"| **{r['name']}** | {r['reg_number']} | {r['course_name']} | ₹{float(r.get('total_due',0)):,.0f} | ₹{float(r.get('total_paid',0)):,.0f} | **₹{float(r.get('balance',0)):,.0f}** |\n" for r in rows)
                return f"💰 **Fee Defaulters** ({len(rows)} students):\n\n{header}{table}" if rows else "✅ No fee defaulters found — all students are up to date!"
            return "💰 No fee structure data configured yet."

        # Staff by department
        if any(k in msg for k in ["staff in", "staff of", "faculty in", "faculty of", "list staff", "show staff", "all staff"]):
            result = execute_tool("get_staff_by_department", {}, user)
            if result.get("success") and result.get("data"):
                rows = result["data"]
                header = "| Name | Designation | Department | Qualification |\n|---|---|---|---|\n"
                table = "".join(f"| **{r['name']}** | {r['designation']} | {r.get('department_name','N/A')} | {r.get('qualification','N/A')} |\n" for r in rows)
                return f"👨‍🏫 **Staff List** ({len(rows)} members):\n\n{header}{table}"
            return "👨‍🏫 No staff records found."

        # Find student by name
        name_match = _re.search(r'(?:find|search|student named?|look up student|who is)\s+(.+?)(?:\?|$)', msg)
        if name_match and any(k in msg for k in ["find student", "search student", "student named", "look up student", "who is"]):
            name = name_match.group(1).strip()
            result = execute_tool("get_student_by_name", {"name": name}, user)
            if result.get("success") and result.get("data"):
                rows = result["data"]
                if len(rows) == 1:
                    s = rows[0]
                    return f"""👤 **Student Profile: {s['name']}**

| Field | Value |
|---|---|
| **Reg Number** | {s['reg_number']} |
| **Roll Number** | {s['roll_number']} |
| **Course** | {s['course_name']} |
| **Department** | {s['department_name']} |
| **Section** | {s['section_name']} |
| **CGPA** | {s.get('cgpa', 0)} |
| **Category** | {s.get('student_category', 'N/A')} |
| **Community** | {s.get('caste_community', 'N/A')} |
| **Email** | {s.get('email', 'N/A')} |
| **Phone** | {s.get('phone', 'N/A')} |"""
                else:
                    lines = [f"• **{s['name']}** ({s['reg_number']}) — {s['course_name']}, CGPA: {s.get('cgpa',0)}" for s in rows]
                    return f"🔍 Found **{len(rows)} students** matching '{name}':\n" + "\n".join(lines)
            return f"🔍 No student found matching '{name}'."

        # Sections list
        if any(k in msg for k in ["section list", "all section", "list section", "show section"]):
            result = execute_tool("get_sections_list", {}, user)
            if result.get("success") and result.get("data"):
                rows = result["data"]
                header = "| Section | Course | Dept | Semester | Students |\n|---|---|---|---|---|\n"
                table = "".join(f"| **{r['section_name']}** | {r['course_name']} | {r['department_name']} | {r.get('semester_number','N/A')} | {r['student_count']} |\n" for r in rows)
                return f"📋 **Sections** ({len(rows)} total):\n\n{header}{table}"
            return "📋 No sections found."

        # Dashboard / combined summary
        if any(k in msg for k in ["college summary", "dashboard", "overview", "full summary"]):
            result = execute_tool("get_combined_summary", {}, user)
            if result.get("success") and result.get("data"):
                s = result["data"]["summary"]
                depts = result["data"].get("departments", [])
                dept_table = ""
                if depts:
                    dept_table = "\n\n**By Department:**\n| Department | Students | Staff |\n|---|---|---|\n"
                    dept_table += "".join(f"| {d['name']} | {d['students']} | {d['staff']} |\n" for d in depts)
                return f"""📊 **College Dashboard Summary**

| Metric | Value |
|---|---|
| 🎓 Active Students | **{s['active_students']}** |
| 👨‍🏫 Active Staff | **{s['active_staff']}** |
| 🏛️ Departments | **{s['departments']}** |
| 📚 Courses | **{s['courses']}** |
| 📖 Subjects | **{s['subjects']}** |
| 💰 Total Fees Collected | **₹{s['total_fees_collected']:,.2f}** |
| 📅 Avg Attendance | **{s['avg_attendance_pct']}%** |{dept_table}"""
            return "📊 Summary data unavailable."

        # Attendance Write (mark present/absent)
        import re
        att_match = re.search(r'mark\s+(.+?)\s+(present|absent|od)\s+(?:for\s+)?(.+?)(?:\s+(?:on|today|for)\s+(.+))?$', msg)

        if att_match:
            student_name = att_match.group(1).strip()
            att_status = {"present": "P", "absent": "A", "od": "OD"}[att_match.group(2)]
            subject_name = att_match.group(3).strip()
            date_str = att_match.group(4).strip() if att_match.group(4) else None
            if not date_str or date_str == "today":
                from datetime import date
                date_str = date.today().isoformat()
            # Find student and subject
            student = query("SELECT student_id, name FROM student WHERE LOWER(name) LIKE %s AND status='active' LIMIT 1",
                            (f"%{student_name}%",), fetchone=True)
            subject = query("SELECT subject_id, name FROM subject WHERE LOWER(name) LIKE %s LIMIT 1",
                            (f"%{subject_name}%",), fetchone=True)
            if student and subject:
                result = execute_tool("update_attendance", {
                    "student_id": student["student_id"],
                    "subject_id": subject["subject_id"],
                    "date": date_str,
                    "status": att_status
                }, user)
                if result.get("needs_confirmation"):
                    return result  # Return the confirmation dict directly
                return "✅ Attendance request processed."
            elif not student:
                return f"❌ Could not find student matching **{student_name}**."
            else:
                return f"❌ Could not find subject matching **{subject_name}**."

        # Help
        if any(k in msg for k in ["help", "what can you do", "what can you", "capabilities", "commands"]):
            return """👋 Hi! I'm **AIRA**, your AI assistant for the College Management System. Here's what I can help you with:

📊 **Student Info**: "How many students?", "List students", "Student profile report"
🏫 **Departments**: "How many departments?", "Department summary"  
👨‍🏫 **Staff**: "How many staff members?", "List staff"
📚 **Courses**: "How many courses?", "List courses"
📖 **Subjects**: "How many subjects?"
📅 **Attendance**: "Overall attendance", "Attendance report"
💰 **Fees**: "Total fees collected?", "Fee structure report"
📝 **Marks**: "Marks report", "Show marks"

**📋 Advanced Reports:**
🎯 **Eligibility**: "Eligibility report", "Eligible students"
🏷️ **Categories**: "Category wise report", "Centac students"
🎓 **Scholarships**: "Scholarship report", "Caste wise scholarships"
🏆 **Activities**: "Extracurricular activities", "Technical activities"
📊 **CGPA**: "CGPA report", "Student profile report"
💰 **Fee Structure**: "Fee structure", "Fee breakdown"

**✏️ Write Actions (with confirmation):**
📅 **Attendance**: "Mark John present for DBMS today"

> 💡 **Tip**: For more advanced queries, configure a Gemini API key in Settings → LLM Config."""

        # Default fallback with richer suggestions
        return f"""🤖 I understand you asked: *"{message}"*

I didn't find a direct match, but I'm here to help! Here are things I can answer:

| Query Type | Example |
|---|---|
| Students | "List all students", "How many students?" |
| Staff | "Show staff list", "How many teachers?" |
| Attendance | "Attendance report", "Students below 75% attendance" |
| Marks | "Marks report", "Show marks for semester 1" |
| CGPA | "CGPA report", "Top 10 students by CGPA" |
| Fees | "Fee defaulters", "Fee structure report", "Total fees collected" |
| Reports | "Eligibility report", "Scholarship report", "Category wise report" |
| Activities | "Extracurricular activities", "Technical events" |
| Write | "Mark [name] present for [subject] today" |

> 💡 For full natural language understanding, configure a **Gemini API key** in Settings → LLM Config."""

    except Exception as e:
        return f"⚠️ Sorry, I encountered an error while processing your query: {str(e)}"

@aira_bp.route("/tools", methods=["GET"])
@login_required
def get_tools():
    return success(MCP_TOOLS)

@aira_bp.route("/ollama-models", methods=["GET"])
@login_required
def get_ollama_models():
    """Proxy Ollama's /api/tags to return available local models.
    Allows frontend to fetch models without direct browser→Ollama CORS issues.
    """
    ollama_url = "http://localhost:11434"
    try:
        resp = http_requests.get(f"{ollama_url}/api/tags", timeout=4)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("models", [])
        # Return simplified list: name + size
        simplified = [
            {
                "name": m.get("name"),
                "size_bytes": m.get("size", 0),
                "size_gb": round(m.get("size", 0) / 1e9, 2) if m.get("size") else None,
                "family": m.get("details", {}).get("family", ""),
            }
            for m in models
        ]
        return success({"models": simplified, "count": len(simplified)})
    except Exception as e:
        return error(f"Could not reach Ollama at {ollama_url}: {str(e)}", 503)

import ai_client

@aira_bp.route("/test", methods=["GET"])
@login_required
def test_aira_connection():
    """Verify if AIRA (Ollama backend) is reachable and model is available."""
    if not ai_client.check_ollama_status():
        return error("Could not connect to Ollama. Is it running?")
        
    cfg = ai_client._get_active_config()
    model = cfg.get("model", ai_client.DEFAULT_MODEL)
    
    if not ai_client.check_model_exists(model):
        return error(f"Ollama is running, but model '{model}' is not found.")
        
    return success(message=f"Connection successful to {model}")

@aira_bp.route("/execute-tool", methods=["POST"])
@login_required
def run_tool():
    data = request.get_json()
    tool_name = data.get("tool_name")
    tool_args = data.get("args", {})
    result = execute_tool(tool_name, tool_args, request.current_user)
    # Log the action
    execute("""INSERT INTO aira_action_log (user_id, action_type, entity_type, action_details, status)
               VALUES (%s,%s,%s,%s,%s)""",
            (request.current_user["user_id"], "tool_call", tool_name,
             json.dumps({"args": tool_args, "result_count": len(result.get("data", []))}),
             "success" if result["success"] else "error"))
    return success(result)


from flask import send_from_directory
import os

@aira_bp.route("/reports/<path:filename>", methods=["GET"])
def download_report(filename):
    # Public download route allowing direct browser clicks without JWT
    safe_dir = os.path.abspath(REPORTS_DIR)
    file_path = os.path.abspath(os.path.join(REPORTS_DIR, filename))
    if not file_path.startswith(safe_dir) or not os.path.exists(file_path):
        return error("Report not found", 404)
    return send_from_directory(safe_dir, filename)


@aira_bp.route("/confirm-action", methods=["POST"])
@login_required
def confirm_action():
    """Execute a previously pending write action after user confirmation."""
    data = request.get_json()
    action_id = data.get("action_id")
    if not action_id:
        return error("action_id is required")

    # Fetch the pending action
    action = query(
        "SELECT * FROM aira_action_log WHERE action_id=%s AND status='pending' AND user_id=%s",
        (action_id, request.current_user["user_id"]), fetchone=True
    )
    if not action:
        return error("Action not found or already processed", 404)

    try:
        details = json.loads(action["action_details"])
        entity_type = action["entity_type"]

        if entity_type == "attendance":
            # Execute the attendance update
            student_id = details["student_id"]
            subject_id = details["subject_id"]
            date = details["date"]
            att_status = details.get("status", "P")
            # Check if record exists
            existing = query(
                "SELECT attendance_id FROM attendance WHERE student_id=%s AND subject_id=%s AND attendance_date=%s",
                (student_id, subject_id, date), fetchone=True
            )
            if existing:
                execute("UPDATE attendance SET status=%s WHERE attendance_id=%s",
                        (att_status, existing["attendance_id"]))
            else:
                # Need section_id and period_id — get from student context
                student = query("SELECT section_id FROM student WHERE student_id=%s", (student_id,), fetchone=True)
                section_id = student["section_id"] if student else None
                period = query("SELECT period_id FROM period_definition ORDER BY period_number LIMIT 1", fetchone=True)
                period_id = period["period_id"] if period else None
                ay = query("SELECT academic_year_id FROM academic_year WHERE is_current=1 LIMIT 1", fetchone=True)
                ay_id = ay["academic_year_id"] if ay else None
                execute(
                    """INSERT INTO attendance (student_id, subject_id, section_id, period_id,
                       academic_year_id, attendance_date, status) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (student_id, subject_id, section_id, period_id, ay_id, date, att_status)
                )
            # Mark action as completed
            execute("UPDATE aira_action_log SET status='completed' WHERE action_id=%s", (action_id,))
            return success({"completed": True}, "✅ Attendance updated successfully!")
        else:
            return error(f"Unsupported action type: {entity_type}")
    except Exception as e:
        execute("UPDATE aira_action_log SET status='error' WHERE action_id=%s", (action_id,))
        return error(f"Failed to execute action: {str(e)}")


@aira_bp.route("/cancel-action", methods=["POST"])
@login_required
def cancel_action():
    """Cancel a previously pending write action."""
    data = request.get_json()
    action_id = data.get("action_id")
    if not action_id:
        return error("action_id is required")
    execute(
        "UPDATE aira_action_log SET status='cancelled' WHERE action_id=%s AND status='pending' AND user_id=%s",
        (action_id, request.current_user["user_id"])
    )
    return success(message="Action cancelled")

@aira_bp.route("/conversations", methods=["GET"])
@login_required
def get_conversations():
    convs = query("""SELECT * FROM aira_conversation WHERE user_id=%s AND expires_at > NOW()
                     ORDER BY updated_at DESC LIMIT 20""",
                  (request.current_user["user_id"],))
    return success(convs)

@aira_bp.route("/config", methods=["GET"])
@login_required
def get_config():
    config = query("SELECT config_id, provider, selected_model, fallback_provider, fallback_model, temperature, max_tokens FROM llm_config LIMIT 1", fetchone=True)
    return success(config)

@aira_bp.route("/config", methods=["POST"])
@login_required
def save_config():
    data = request.get_json()
    existing = query("SELECT config_id FROM llm_config LIMIT 1", fetchone=True)
    if existing:
        execute("""UPDATE llm_config SET provider=%s, api_key_encrypted=%s, selected_model=%s,
                   fallback_provider=%s, fallback_model=%s, temperature=%s, max_tokens=%s, updated_at=NOW()
                   WHERE config_id=%s""",
                (data.get("provider"), data.get("api_key"), data.get("selected_model"),
                 data.get("fallback_provider", "ollama"), data.get("fallback_model", "gemma4:e4b"),
                 data.get("temperature", 0.7), data.get("max_tokens", 2048), existing["config_id"]))
    else:
        execute("""INSERT INTO llm_config (provider, api_key_encrypted, selected_model, fallback_provider, fallback_model, temperature, max_tokens)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (data.get("provider"), data.get("api_key"), data.get("selected_model"),
                 data.get("fallback_provider", "ollama"), data.get("fallback_model", "gemma4:e4b"),
                 data.get("temperature", 0.7), data.get("max_tokens", 2048)))
    return success(message="LLM configuration saved")

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
    
    # Create word-wrapped paragraphs for headers and content so it fits on A4
    table_data = [[Paragraph(f"<b>{h}</b>", styles['Normal']) for h in headers]]
    for row in data:
        # Wrap each cell content in a Paragraph so long text (like emails) wraps inside the column
        table_data.append([Paragraph(str(row.get(h, "")), styles['Normal']) for h in headers])
        
    # Calculate column widths to fit A4 layout
    # letter/A4 width is ~612pts, minus ~72pts margin = 540pts usable
    usable_width = 540
    col_width = usable_width / max(len(headers), 1)
        
    t = Table(table_data, colWidths=[col_width] * len(headers))
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
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

    data = []
    # Reuse the correct queries from existing MCP tools instead of hardcoding broken SQL
    if rt == "students" or rt == "cgpa":
        res = execute_tool("generate_student_profile_report", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "fees":
        res = execute_tool("generate_fee_structure_report", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "defaulter":
        res = execute_tool("get_fee_defaulters", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "attendance":
        res = execute_tool("generate_attendance_report", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "department":
        res = execute_tool("get_department_summary", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "scholarship":
        res = execute_tool("generate_scholarship_report", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "eligibility":
        res = execute_tool("generate_eligibility_report", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "marks":
        res = execute_tool("generate_marks_report", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "category":
        res = execute_tool("generate_category_wise_report", tool_args, user)
        if res.get("success"): data = res["data"]
    elif rt == "extracurricular":
        res = execute_tool("generate_extracurricular_report", tool_args, user)
        if res.get("success"): data = res["data"]
    else:
        # Fallback for general
        res = execute_tool("generate_student_profile_report", tool_args, user)
        if res.get("success"): data = res["data"]

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


def _execute_send_whatsapp_notification(tool_args: dict, user: dict) -> dict:
    import requests
    numbers = tool_args.get('phone_numbers', [])
    message = tool_args.get('message', '')
    
    if not numbers or not message:
        return {"error": "Phone numbers and message are required."}
        
    NODE_SERVICE_URL = "http://localhost:4000"
    success_count = 0
    failures = []
    
    for number in numbers:
        try:
            payload = {"number": number, "message": message}
            response = requests.post(f"{NODE_SERVICE_URL}/send", json=payload, timeout=15)
            
            if response.status_code == 200:
                success_count += 1
            else:
                failures.append({"number": number, "error": response.text})
        except Exception as e:
            failures.append({"number": number, "error": str(e)})

    return {
        "success": True,
        "result": {
            "total_attempted": len(numbers),
            "successful": success_count,
            "failed": len(failures),
            "failures": failures
        },
        "message": f"Successfully initiated WhatsApp sending. Delivered to {success_count}/{len(numbers)} numbers.",
        "type": "whatsapp_report"
    }

def _execute_beautiful_pdf_report(tool_args: dict, user: dict) -> dict:
    """
    Execute the generate_beautiful_pdf_report MCP tool.
    Delegates to the pdf_reports blueprint's data builders and WeasyPrint renderer.
    """
    from app.routes.pdf_reports import (
        _render_pdf,
        _build_student_full_profile,
        _build_fee_defaulters,
        _build_attendance_summary,
    )

    template   = tool_args.get("template", "")
    student_id = tool_args.get("student_id")

    try:
        if template == "student_full_profile":
            if not student_id:
                return {"response_type": "text", "message": "❌ Please provide a student ID or name for the full profile report."}
            ctx = _build_student_full_profile(int(student_id))
            if not ctx:
                return {"response_type": "text", "message": f"❌ No student found with ID {student_id}."}
            filename = _render_pdf("student_full_profile.html", ctx)
            label    = f"Full Profile — {ctx['student']['name']}"

        elif template == "fee_defaulters":
            ctx      = _build_fee_defaulters(
                academic_year_id=tool_args.get("academic_year_id"),
                department_id=tool_args.get("department_id"),
            )
            filename = _render_pdf("fee_defaulters.html", ctx)
            label    = f"Fee Defaulters ({ctx['academic_year']})"

        elif template == "attendance_summary":
            ctx      = _build_attendance_summary(
                section_id=tool_args.get("section_id"),
                student_id=tool_args.get("student_id"),
                department_id=tool_args.get("department_id"),
                subject_id=tool_args.get("subject_id"),
                date_from=tool_args.get("date_from"),
                date_to=tool_args.get("date_to"),
            )
            filename = _render_pdf("attendance_summary.html", ctx)
            label    = f"Attendance Summary"

        else:
            return {"response_type": "text", "message": f"❌ Unknown template: '{template}'. Use student_full_profile, fee_defaulters, or attendance_summary."}

    except Exception as e:
        return {"response_type": "text", "message": f"❌ PDF generation failed: {str(e)}"}

    download_url = f"/api/pdf-reports/download/{filename}"
    return {
        "response_type": "report",
        "filename": filename,
        "format": "PDF",
        "download_url": download_url,
        "preview_url":  download_url,
        "message": f"✅ **{label}** — PDF is ready!\n\n📄 [Download PDF]({download_url})\n\n> 🎨 This report was generated with professional A4 styling including college letterhead, page numbers, and institutional formatting."
    }

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
