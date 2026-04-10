"""
reset_admin.py — Permanently fix superadmin password hash
=========================================================
Run from Main/Backend to use the correct uv virtual environment:

  cd Main\\Backend
  uv run python ..\\..\\reset_admin.py

This script:
  1. Generates a fresh Python-bcrypt hash for Admin@123
  2. Updates the user_account table directly in MySQL
  3. Updates seed.sql with the correct hash for future fresh installs
  4. Verifies the login works after the fix

Run this whenever the superadmin password stops working (hash mismatch after
re-importing seed.sql with a PHP-generated or mis-copied hash).
"""

import os
import sys
import re

# ── Load env (DB credentials) ──────────────────────────────────────────────────
env_path = os.path.join(os.path.dirname(__file__), "Main", "Backend", ".env")
if not os.path.exists(env_path):
    # Try relative from Main/Backend if run from there
    env_path = os.path.join(os.path.dirname(__file__), ".env")

if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "college_management")
TARGET_PASSWORD = "Admin@123"

print("\n" + "="*55)
print("  🔐  College Management — Admin Password Reset")
print("="*55)

# ── 1. Generate fresh Python-bcrypt hash ──────────────────────────────────────
try:
    import bcrypt
except ImportError:
    print("ERROR: bcrypt not found. Run: uv pip install bcrypt")
    sys.exit(1)

fresh_hash = bcrypt.hashpw(TARGET_PASSWORD.encode(), bcrypt.gensalt(12)).decode()
print(f"\n[1/4] Generated fresh bcrypt hash:\n      {fresh_hash}")

# ── 2. Update MySQL database ───────────────────────────────────────────────────
try:
    import pymysql
except ImportError:
    print("ERROR: pymysql not found. Run: uv pip install pymysql")
    sys.exit(1)

print(f"\n[2/4] Connecting to MySQL at {DB_HOST}:{DB_PORT}/{DB_NAME} ...")
try:
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME
    )
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE user_account SET password_hash = %s WHERE username = 'superadmin'",
            (fresh_hash,)
        )
        rows = cur.rowcount
    conn.commit()
    conn.close()
    if rows == 0:
        print("  ⚠️  No superadmin user found in DB. Run seed.sql first.")
    else:
        print(f"  ✅  Updated password_hash in user_account table (rows affected: {rows})")
except Exception as e:
    print(f"  ❌  DB error: {e}")
    sys.exit(1)

# ── 3. Update seed.sql with the new hash for future fresh installs ─────────────
print(f"\n[3/4] Updating seed.sql with new hash ...")
seed_path = os.path.join(os.path.dirname(__file__), "Main", "Backend", "database", "seed.sql")
if not os.path.exists(seed_path):
    seed_path = os.path.join(os.path.dirname(__file__), "database", "seed.sql")

if os.path.exists(seed_path):
    with open(seed_path, "r") as f:
        content = f.read()
    # Replace the hash line (the $2b$... hash inside the INSERT statement)
    updated = re.sub(
        r"('\$2[aby]\$[0-9]+\$[A-Za-z0-9./]{53}')",
        f"'{fresh_hash}'",
        content
    )
    with open(seed_path, "w") as f:
        f.write(updated)
    print(f"  ✅  seed.sql updated at: {seed_path}")
else:
    print("  ⚠️  Could not find seed.sql — skipping file update.")

# ── 4. Verify the fix ──────────────────────────────────────────────────────────
print(f"\n[4/4] Verifying password against stored hash ...")
try:
    conn2 = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME
    )
    with conn2.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT password_hash FROM user_account WHERE username = 'superadmin'")
        row = cur.fetchone()
    conn2.close()

    if row and bcrypt.checkpw(TARGET_PASSWORD.encode(), row["password_hash"].encode()):
        print("  ✅  Password verification PASSED — login will work!")
    else:
        print("  ❌  Password verification FAILED — something went wrong.")
        sys.exit(1)
except Exception as e:
    print(f"  ❌  Verification error: {e}")
    sys.exit(1)

print("\n" + "="*55)
print("  🎉  Done! Login with: superadmin / Admin@123")
print("="*55 + "\n")
