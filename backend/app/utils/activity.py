from app.db import execute


def log_activity(user_id: int, action: str, entity_type: str, entity_id: int = None, details: str = None):
    """Insert an entry into the activity_log table for audit trail purposes."""
    try:
        execute(
            """INSERT INTO activity_log (user_id, action, entity_type, entity_id, details)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, action, entity_type, entity_id, details)
        )
    except Exception:
        pass  # Activity logging must never break the main flow
