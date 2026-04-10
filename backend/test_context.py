import sys
sys.path.append('.')

from app.utils.auth import generate_token, hash_password
from app.routes.aira import _get_db_context, get_user_scope
from app.utils.db import query

user = {'user_id': 136, 'role': 'staff', 'ref_id': 500}
print("User scope:", get_user_scope(user))

try:
    ctx = _get_db_context(user)
    print("Database context length:", len(ctx))
except Exception as e:
    import traceback
    traceback.print_exc()

print("DONE")
