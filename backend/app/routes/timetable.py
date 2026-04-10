from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import login_required, roles_required
from app.utils.response import success, error

timetable_bp = Blueprint("timetable", __name__)

@timetable_bp.route("/", methods=["GET"])
@login_required
def get_timetable():
    section_id = request.args.get("section_id")
    ay_id = request.args.get("academic_year_id")
    if not section_id:
        return error("section_id is required")
    sql = """SELECT t.*, sub.name as subject_name, sub.code as subject_code,
             s.name as staff_name, r.name as room_name, p.period_number,
             p.start_time, p.end_time, p.label as period_label
             FROM timetable t
             JOIN subject sub ON t.subject_id=sub.subject_id
             JOIN staff s ON t.staff_id=s.staff_id
             LEFT JOIN room r ON t.room_id=r.room_id
             JOIN period_definition p ON t.period_id=p.period_id
             WHERE t.section_id=%s"""
    params = [section_id]
    if ay_id:
        sql += " AND t.academic_year_id=%s"; params.append(ay_id)
    sql += " ORDER BY FIELD(t.day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'), p.period_number"
    return success(query(sql, params))

@timetable_bp.route("/", methods=["POST"])
@roles_required("super_admin", "admin", "hod")
def add_timetable_entry():
    data = request.get_json()
    tid = execute("""INSERT INTO timetable (section_id, subject_id, staff_id, room_id, period_id, academic_year_id, day_of_week)
                     VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                  (data["section_id"], data["subject_id"], data["staff_id"],
                   data.get("room_id"), data["period_id"], data["academic_year_id"], data["day_of_week"]))
    return success({"timetable_id": tid}, "Timetable entry added", 201)

@timetable_bp.route("/<int:timetable_id>", methods=["DELETE"])
@roles_required("super_admin", "admin", "hod")
def delete_timetable_entry(timetable_id):
    execute("DELETE FROM timetable WHERE timetable_id=%s", (timetable_id,))
    return success(message="Entry removed")

@timetable_bp.route("/periods", methods=["GET"])
@login_required
def get_periods():
    return success(query("SELECT * FROM period_definition ORDER BY period_number"))

@timetable_bp.route("/periods", methods=["POST"])
@roles_required("super_admin", "admin")
def add_period():
    data = request.get_json()
    pid = execute("INSERT INTO period_definition (college_id, period_number, start_time, end_time, label) VALUES (%s,%s,%s,%s,%s)",
                  (data["college_id"], data["period_number"], data["start_time"], data["end_time"], data.get("label")))
    return success({"period_id": pid}, "Period added", 201)

@timetable_bp.route("/rooms", methods=["GET"])
@login_required
def get_rooms():
    return success(query("SELECT * FROM room ORDER BY name"))

@timetable_bp.route("/rooms", methods=["POST"])
@roles_required("super_admin", "admin")
def add_room():
    data = request.get_json()
    rid = execute("INSERT INTO room (college_id, name, type, capacity, building, floor_number) VALUES (%s,%s,%s,%s,%s,%s)",
                  (data["college_id"], data["name"], data["type"], data.get("capacity"), data.get("building"), data.get("floor_number")))
    return success({"room_id": rid}, "Room added", 201)
