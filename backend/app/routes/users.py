from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import roles_required, hash_password
from app.utils.response import success, error
from app.utils.activity import log_activity

users_bp = Blueprint("users", __name__)

@users_bp.route("", methods=["GET"])
@roles_required("super_admin")
def get_users():
    sql = """
        SELECT u.user_id, u.username, u.is_active, r.role_name, 
               s.name as staff_name, s.department_id, d.name as department_name
        FROM user_account u
        JOIN role r ON u.role_id = r.role_id
        LEFT JOIN staff s ON u.ref_id = s.staff_id AND u.ref_type = 'staff'
        LEFT JOIN department d ON s.department_id = d.department_id
        WHERE u.ref_type = 'staff'
    """
    users = query(sql)
    return success(users)

@users_bp.route("/<int:user_id>/role", methods=["PUT"])
@roles_required("super_admin")
def update_user_role(user_id):
    data = request.get_json()
    new_role_name = data.get("role_name")
    
    role = query("SELECT role_id FROM role WHERE role_name=%s", (new_role_name,), fetchone=True)
    if not role:
        return error("Invalid role specified", 400)
        
    execute("UPDATE user_account SET role_id=%s WHERE user_id=%s", (role['role_id'], user_id))
    log_activity(request.current_user["user_id"], "update", "user_account", user_id, f"Changed role to {new_role_name}")
    return success(message="User role updated successfully")

@users_bp.route("/<int:user_id>/reset-password", methods=["PUT"])
@roles_required("super_admin")
def reset_user_password(user_id):
    data = request.get_json()
    new_password = data.get("new_password")
    new_username = data.get("new_username")
    
    if not new_password and not new_username:
        return error("Nothing to update", 400)
        
    updates = []
    params = []
    
    if new_username:
        # Check if username exists
        existing = query("SELECT user_id FROM user_account WHERE username=%s AND user_id!=%s", (new_username, user_id), fetchone=True)
        if existing:
            return error("Username already taken", 400)
        updates.append("username=%s")
        params.append(new_username)
        
    if new_password:
        updates.append("password_hash=%s")
        params.append(hash_password(new_password))
        
    params.append(user_id)
    
    if updates:
        sql = f"UPDATE user_account SET {', '.join(updates)} WHERE user_id=%s"
        execute(sql, tuple(params))
        log_activity(request.current_user["user_id"], "update", "user_account", user_id, "Reset password/username by Super Admin")
        
    return success(message="User credentials updated successfully")
