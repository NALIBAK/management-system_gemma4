from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.url_map.strict_slashes = False  # Prevent trailing-slash redirects (breaks CORS preflight)

    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register all blueprints
    from app.routes.auth import auth_bp
    from app.routes.college import college_bp
    from app.routes.courses import courses_bp
    from app.routes.students import students_bp
    from app.routes.staff import staff_bp
    from app.routes.timetable import timetable_bp
    from app.routes.marks import marks_bp
    from app.routes.attendance import attendance_bp
    from app.routes.fees import fees_bp
    from app.routes.reports import reports_bp
    from app.routes.aira import aira_bp
    from app.routes.notifications import notifications_bp
    from app.routes.users import users_bp
    from app.routes.pdf_reports import pdf_report_bp
    from app.routes.whatsapp import whatsapp_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(college_bp, url_prefix="/api/college")
    app.register_blueprint(courses_bp, url_prefix="/api/courses")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(staff_bp, url_prefix="/api/staff")
    app.register_blueprint(timetable_bp, url_prefix="/api/timetable")
    app.register_blueprint(marks_bp, url_prefix="/api/marks")
    app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
    app.register_blueprint(fees_bp, url_prefix="/api/fees")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(aira_bp, url_prefix="/api/aira")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(pdf_report_bp, url_prefix="/api/pdf-reports")
    app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")

    # Ensure reports archive directory exists
    import os
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "reports_archive"), exist_ok=True)

    @app.route("/api/health")
    def health():
        return {"status": "ok", "message": "College Management API is running"}

    return app
