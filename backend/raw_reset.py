import pymysql
import bcrypt

try:
    con = pymysql.connect(host="localhost", user="root", password="", db="college_management")
    cur = con.cursor(pymysql.cursors.DictCursor)
    
    hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
    
    cur.execute("SELECT * FROM user_account WHERE role='super_admin' LIMIT 1")
    user = cur.fetchone()
    
    if user:
        print(f"Found Super Admin: {user['username']}")
        cur.execute("UPDATE user_account SET password_hash=%s WHERE user_id=%s", (hashed, user['user_id']))
        con.commit()
        print("Password reset to admin123")
    else:
        print("No super_admin found!")
        cur.execute("SELECT username, role FROM user_account")
        users = cur.fetchall()
        print("Available users:", users)
    
    con.close()
except Exception as e:
    print(f"Error: {e}")
