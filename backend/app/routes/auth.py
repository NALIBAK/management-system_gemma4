from flask import Blueprint, request
from app.db import query, execute
from app.utils.auth import hash_password, check_password, generate_token, login_required
from app.utils.response import success, error

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error("Username and password are required")

    user = query(
        """SELECT u.*, r.role_name FROM user_account u
           JOIN role r ON u.role_id = r.role_id
           WHERE u.username = %s AND u.is_active = 1""",
        (username,), fetchone=True
    )

    if not user or not check_password(password, user["password_hash"]):
        return error("Invalid username or password", 401)

    # Update last login
    execute("UPDATE user_account SET last_login = NOW() WHERE user_id = %s", (user["user_id"],))

    token = generate_token(
        user_id=user["user_id"],
        role=user["role_name"],
        ref_id=user["ref_id"],
        ref_type=user["ref_type"]
    )

    return success({
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role_name"],
            "ref_id": user["ref_id"],
            "ref_type": user["ref_type"]
        }
    }, "Login successful")

@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = request.current_user
    db_user = query(
        """SELECT u.user_id, u.username, u.is_active, u.last_login, r.role_name
           FROM user_account u JOIN role r ON u.role_id = r.role_id
           WHERE u.user_id = %s""",
        (user["user_id"],), fetchone=True
    )
    return success(db_user)

@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json()
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    if not old_password or not new_password:
        return error("Both old and new passwords are required")

    user = query(
        "SELECT password_hash FROM user_account WHERE user_id = %s",
        (request.current_user["user_id"],), fetchone=True
    )

    if not check_password(old_password, user["password_hash"]):
        return error("Old password is incorrect", 401)

    execute(
        "UPDATE user_account SET password_hash = %s WHERE user_id = %s",
        (hash_password(new_password), request.current_user["user_id"])
    )
    return success(message="Password changed successfully")

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    # JWT is stateless; client should discard token
    return success(message="Logged out successfully")
