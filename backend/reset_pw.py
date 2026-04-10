from app.utils.db import query
from app.utils.auth import hash_password

hashed = hash_password('admin123')
user = query("SELECT * FROM user_account WHERE role_name='super_admin' LIMIT 1", fetchone=True)
if user:
    print(f"Found Super Admin: {user['username']}")
    query("UPDATE user_account SET password_hash=%s WHERE user_id=%s", (hashed, user['user_id']))
    print("Password reset to admin123")
else:
    print("No super_admin found!")
    users = query("SELECT username, role_name FROM user_account")
    print("Available users:", users)
