from app import create_app
from app.db import execute
from app.utils.auth import hash_password

app = create_app()

with app.app_context():
    new_hash = hash_password("Admin@123")
    execute("UPDATE user_account SET password_hash = %s WHERE username = 'superadmin'", (new_hash,))
    print("Password for 'superadmin' reset to 'Admin@123'")
