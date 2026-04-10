import pymysql
import pymysql.cursors
from config import Config

def get_db():
    """Get a new database connection."""
    connection = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    return connection

def query(sql, params=None, fetchone=False, commit=False):
    """Execute a query and return results."""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            if commit:
                conn.commit()
                return cursor.lastrowid
            if fetchone:
                return cursor.fetchone()
            return cursor.fetchall()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute(sql, params=None):
    """Execute a write query (INSERT/UPDATE/DELETE)."""
    return query(sql, params, commit=True)
