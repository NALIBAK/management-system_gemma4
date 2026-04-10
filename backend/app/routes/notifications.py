from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required
from app.utils.response import success, error

notifications_bp = Blueprint("notifications", __name__)

# --- Templates ---
@notifications_bp.route("/templates", methods=["GET"])
@login_required
def get_templates():
    user = request.current_user
    templates = query("SELECT * FROM notification_template WHERE staff_id=%s ORDER BY created_at DESC",
                      (user.get("ref_id"),))
    return success(templates)

@notifications_bp.route("/templates", methods=["POST"])
@login_required
def create_template():
    data = request.get_json()
    user = request.current_user
    tid = execute("""INSERT INTO notification_template (staff_id, title, content_template, channel_type)
                     VALUES (%s,%s,%s,%s)""",
                  (user.get("ref_id"), data["title"], data["content_template"],
                   data.get("channel_type", "whatsapp")))
    return success({"template_id": tid}, "Template created", 201)

@notifications_bp.route("/templates/<int:template_id>", methods=["PUT"])
@login_required
def update_template(template_id):
    data = request.get_json()
    execute("UPDATE notification_template SET title=%s, content_template=%s, channel_type=%s WHERE template_id=%s",
            (data["title"], data["content_template"], data.get("channel_type", "whatsapp"), template_id))
    return success(message="Template updated")

@notifications_bp.route("/templates/<int:template_id>", methods=["DELETE"])
@login_required
def delete_template(template_id):
    execute("DELETE FROM notification_template WHERE template_id=%s", (template_id,))
    return success(message="Template deleted")

# --- Send Notification ---
@notifications_bp.route("/send", methods=["POST"])
@login_required
def send_notification():
    """
    Send a customized notification to one or more students' parents.
    Expects: {student_ids: [], template_id: int, custom_message: str, channel_type: str}
    """
    data = request.get_json()
    user = request.current_user
    student_ids = data.get("student_ids", [])
    channel_type = data.get("channel_type", "whatsapp")
    custom_message = data.get("custom_message", "")
    template_id = data.get("template_id")

    if not student_ids:
        return error("At least one student must be selected")

    template_content = custom_message
    if template_id and not custom_message:
        tmpl = query("SELECT content_template FROM notification_template WHERE template_id=%s",
                     (template_id,), fetchone=True)
        if tmpl:
            template_content = tmpl["content_template"]
            
    if not template_content:
        return error("Either a template or custom message is required")

    sent_count = 0
    failures = []
    import requests
    NODE_SERVICE_URL = "http://localhost:3001"
    
    for student_id in student_ids:
        # Get student info for placeholder substitution
        student = query("""SELECT st.name, st.roll_number, st.reg_number, st.guardian_name, st.guardian_phone,
                           st.email FROM student st WHERE st.student_id=%s""",
                        (student_id,), fetchone=True)
        if not student:
            continue

        # Replace placeholders
        message = template_content
        message = message.replace("{StudentName}", student.get("name", "") or "")
        message = message.replace("{RollNumber}", student.get("roll_number", "") or "")
        message = message.replace("{RegNumber}", student.get("reg_number", "") or "")
        message = message.replace("{GuardianName}", student.get("guardian_name", "") or "")

        # Additional dynamic placeholders from request
        for key, val in data.get("placeholders", {}).items():
            message = message.replace(f"{{{key}}}", str(val) or "")

        delivery_status = 'failed'
        
        # Dispatch logic based on channel
        if channel_type == 'whatsapp':
            phone = student.get("guardian_phone")
            if phone:
                try:
                    payload = {"number": phone, "message": message}
                    res = requests.post(f"{NODE_SERVICE_URL}/send", json=payload, timeout=15)
                    if res.status_code == 200:
                        delivery_status = 'sent'
                        sent_count += 1
                    else:
                        delivery_status = 'failed'
                        err_msg = res.json().get("error", "Unknown error") if "application/json" in res.headers.get("Content-Type", "") else res.text
                        failures.append(f"{student.get('name')}: {err_msg}")
                except requests.exceptions.RequestException as e:
                    delivery_status = 'failed'
                    failures.append(f"{student.get('name')}: Node.js service unreachable")
            else:
                failures.append(f"{student.get('name')}: No guardian phone number")
        else:
            delivery_status = 'failed'
            failures.append(f"{student.get('name')}: Unsupported channel type {channel_type}")

        # Log the notification
        execute("""INSERT INTO notification_log (student_id, sender_staff_id, channel_type, message_content, status)
                   VALUES (%s,%s,%s,%s,%s)""",
                (student_id, user.get("ref_id"), channel_type, message, delivery_status))

    if sent_count == 0 and failures:
        return error("Failed: " + " | ".join(failures))
    elif failures:
        return success({"sent_count": sent_count, "failures": failures}, f"Sent to {sent_count}, but failed for {len(failures)}: " + " | ".join(failures))

    return success({"sent_count": sent_count}, f"Notification sent to {sent_count} student(s)")

# --- Notification History ---
@notifications_bp.route("/history", methods=["GET"])
@login_required
def get_history():
    user = request.current_user
    student_id = request.args.get("student_id")
    sql = """SELECT nl.*, st.name as student_name, st.roll_number,
             s.name as sender_name FROM notification_log nl
             JOIN student st ON nl.student_id=st.student_id
             LEFT JOIN staff s ON nl.sender_staff_id=s.staff_id WHERE 1=1"""
    params = []
    # Staff can only see their own sent notifications
    if user.get("role") == "staff":
        sql += " AND nl.sender_staff_id=%s"; params.append(user.get("ref_id"))
    if student_id:
        sql += " AND nl.student_id=%s"; params.append(student_id)
    sql += " ORDER BY nl.sent_at DESC LIMIT 100"
    return success(query(sql, params))
