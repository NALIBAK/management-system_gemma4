import pymysql
import bcrypt

try:
    con = pymysql.connect(host="localhost", user="root", password="", db="college_management")
    cur = con.cursor(pymysql.cursors.DictCursor)
    
    cur.execute("SELECT * FROM user_account WHERE role_id=4 OR username LIKE 'EMP%' LIMIT 1")
    user = cur.fetchone()
    
    if user:
        hashed = bcrypt.hashpw(b'staff123', bcrypt.gensalt()).decode()
        cur.execute("UPDATE user_account SET password_hash=%s WHERE user_id=%s", (hashed, user['user_id']))
        con.commit()
        print(f"STAFF_FOUND:{user['username']}")
    else:
        print("NO_STAFF_FOUND")
    
    con.close()
except Exception as e:
    print(f"Error: {e}")
