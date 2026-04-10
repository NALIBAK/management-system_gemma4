import sys
sys.path.append('.')

import json
from urllib import request, error
from app.utils.auth import generate_token

token = generate_token(136, 'staff', 500, 'staff')
data = json.dumps({'message': 'how many student'}).encode()
req = request.Request('http://localhost:5000/api/aira/chat', data=data, method='POST')
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {token}')

try:
    res = request.urlopen(req)
    print("SUCCESS")
    print(res.read().decode())
except error.HTTPError as e:
    print(f"HTTP ERROR: {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"ERROR: {e}")
