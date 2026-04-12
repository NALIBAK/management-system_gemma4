import sys
import os

# since we run from backend/, the app module is in current directory
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from aira.router import route_query

app = create_app()

with app.app_context():
    test_user = {
        "user_id": 1,
        "username": "superadmin",
        "role": "super_admin",
        "ref_id": None
    }
    
    scope = {"role": "super_admin", "is_global": True, "dept_ids": [], "course_ids": [], "section_ids": []}
    
    print("Testing AIRA route_query with a sample prompt...")
    try:
        # Prompting for something that requires the get_top_students tool
        res = route_query("Show me top 3 students by CGPA", test_user, [], "Dashboard", scope)
        import json
        print("\n--- Final AIRA Response ---")
        print(json.dumps(res, indent=2))
        print("---------------------------")
    except Exception as e:
        print("\n--- Error Occurred ---")
        import traceback
        traceback.print_exc()
