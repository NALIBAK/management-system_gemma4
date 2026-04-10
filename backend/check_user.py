from app.db import query

user = query("SELECT u.*, r.role_name FROM user_account u JOIN role r ON u.role_id = r.role_id WHERE u.username = 'superadmin'", fetchone=True)
if user:
    print("User exists.")
    print(f"is_active: {user['is_active']}")
    print(f"role_name: {user['role_name']}")
else:
    print("User superadmin not found via join.")

user_direct = query("SELECT * FROM user_account WHERE username = 'superadmin'", fetchone=True)
if user_direct:
    print("Direct user:", user_direct['username'], "is_active:", user_direct['is_active'], "role_id:", user_direct['role_id'])
else:
    print("No direct user")
