import requests
import json

url = "http://localhost:5000/api/staff/"
headers = {
    # Assuming we can get a token or relying on verify_token override for debug?
    # actually, I need a token. I'll login first.
    "Content-Type": "application/json"
}

# Login to get token
login_url = "http://localhost:5000/api/auth/login"
login_data = {"username": "superadmin", "password": "Admin@123"}
session = requests.Session()
try:
    auth_res = session.post(login_url, json=login_data)
    print(f"Login Status: {auth_res.status_code}")
    if auth_res.status_code == 200:
        token = auth_res.json()['data']['token']
        headers["Authorization"] = f"Bearer {token}"
    else:
        print("Login failed:", auth_res.text)
        exit()
except Exception as e:
    print(f"Login connection failed: {e}")
    exit()

# Try to add staff
data = {
    "employee_id": "dummy", # Trigger duplicate if exists
    "name": "Test User",
    "email": "test@example.com",
    "phone": "1234567890",
    "designation": "Prof",
    "qualification": "PhD",
    "department_id": 1, 
    "role_id": 2, # Assuming 2 is staff, need to verify
    "create_account": True,
    "password": "password123",
    "college_id": 1
}

try:
    res = session.post(url, json=data, headers=headers)
    print(f"Status Code: {res.status_code}")
    print("Response:", res.text)
except Exception as e:
    print(f"Request failed: {e}")
