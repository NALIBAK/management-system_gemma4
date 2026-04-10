from app import create_app
from app.db import query
from app.utils.auth import check_password

app = create_app()

with app.app_context():
    user = query("SELECT * FROM user_account WHERE username = 'superadmin'", fetchone=True)
    if user:
        print(f"User found: {user['username']}")
        print(f"Hash in DB: {user['password_hash']}")
        is_valid = check_password("Admin@123", user["password_hash"])
        print(f"Password 'Admin@123' valid? {is_valid}")
    else:
        print("User 'superadmin' not found in database.")
