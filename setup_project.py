import pymysql
import os
import subprocess
import sys

print("=======================================================")
print("  🚀  College Management System — Auto Setup Script 🚀")
print("=======================================================\n")

print("[1] Connecting to XAMPP MySQL...")
try:
    # Connect without targeting a database to create the DB first
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="" # Default XAMPP password is empty
    )
except Exception as e:
    print(f"❌ FAILED: Could not connect to MySQL. Ensure XAMPP is running!\nError: {e}")
    sys.exit(1)

print("[2] Creating Database 'college_management'...")
with conn.cursor() as cur:
    cur.execute("CREATE DATABASE IF NOT EXISTS college_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
conn.close()

print("[3] Injecting Database Schema from backend/database/schema.sql...")
# Connect to the newly created database
conn = pymysql.connect(host="localhost", port=3306, user="root", password="", database="college_management")

# We parse and execute the schema sql
schema_path = os.path.join(os.path.dirname(__file__), "backend", "database", "schema.sql")
with open(schema_path, "r", encoding="utf-8") as f:
    sql_script = f.read()

# execute sql statements divided by semicolon
commands = sql_script.split(';')
with conn.cursor() as cur:
    for cmd in commands:
        if cmd.strip():
            try:
                cur.execute(cmd)
            except Exception as e:
                pass # Ignore drops if table doesn't exist etc.
conn.commit()
conn.close()
print("   ✅ Schema injected successfully.")

print("[4] Generating Initial Data & Super Admin (scripts/populate_db.py)...")
script_path = os.path.join(os.path.dirname(__file__), "scripts", "populate_db.py")
subprocess.run([sys.executable, script_path])

print("\n=======================================================")
print("  🎉  ALL DONE! The System is Fully Initialized!  🎉")
print("=======================================================")
print("  1. Boot the server using:")
print("     uv run python start_server.py")
print("  2. If using Windows to generate PDF reports, ensure GTK3 is installed.")
print("  3. Login with credentials: superadmin / Admin@123")
print("=======================================================\n")
