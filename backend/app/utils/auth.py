"""
app/utils/auth.py — Authentication helpers
==========================================
Provides:
  - hash_password / check_password  : bcrypt wrappers
  - generate_token / decode_token   : JWT helpers
  - login_required                  : decorator for any authenticated route
  - roles_required(*roles)          : decorator for role-gated routes

IMPORTANT — bcrypt compatibility note:
  Passwords must be hashed using Python's `bcrypt` library (as done here via
  bcrypt.hashpw). PHP-generated bcrypt hashes (e.g. from password_hash()) use
  the $2y$ prefix which is NOT compatible with PyBcrypt. Always use this module
  to generate/verify passwords.

  To reset the superadmin password, run:
    uv run python -c "import bcrypt; print(bcrypt.hashpw(b'NewPass@123', bcrypt.gensalt()).decode())"
  Then update the hash in user_account via phpMyAdmin or MySQL CLI.

FIX APPLIED: The login_required decorator previously did not short-circuit on
OPTIONS requests (CORS preflight). This caused the browser to receive a 401
Unauthorized instead of a 200 OK for preflight checks, making every API call
appear to fail with a CORS error. OPTIONS requests are now passed through
without authentication.
"""
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from config import Config


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt. Store the returned string in the DB."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def generate_token(user_id: int, role: str, ref_id: int = None, ref_type: str = None) -> str:
    """Generate a signed JWT token for the given user."""
    payload = {
        "user_id": user_id,
        "role": role,
        "ref_id": ref_id,
        "ref_type": ref_type,
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises jwt.InvalidTokenError on failure."""
    return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])


def get_current_user():
    """Extract and decode the user from the Authorization: Bearer <token> header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        return decode_token(token)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def login_required(f):
    """
    Decorator: requires a valid JWT in Authorization header.
    OPTIONS requests are always allowed through (needed for CORS preflight).
    Sets request.current_user to the decoded token payload.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow CORS preflight requests without authentication
        if request.method == "OPTIONS":
            return f(*args, **kwargs)
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def roles_required(*roles):
    """
    Decorator: requires a valid JWT AND the user's role must be in the given roles list.
    OPTIONS requests are always allowed through (needed for CORS preflight).
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Allow CORS preflight requests without authentication
            if request.method == "OPTIONS":
                return f(*args, **kwargs)
            user = get_current_user()
            if not user:
                return jsonify({"success": False, "message": "Unauthorized"}), 401
            if user.get("role") not in roles:
                return jsonify({"success": False, "message": "Forbidden"}), 403
            request.current_user = user
            return f(*args, **kwargs)
        return decorated
    return decorator
