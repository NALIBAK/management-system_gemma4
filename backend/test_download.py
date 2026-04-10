import requests

# 1. Login to get session cookie
s = requests.Session()
r = s.post("http://localhost:5000/api/auth/login", json={"username": "superadmin", "password": "Admin@123"})
if not r.ok or not r.json().get("success"):
    print("Login failed", r.text)
    exit(1)

# 2. Trigger smart fallback to export the defaulter report
r2 = s.post("http://localhost:5000/api/aira/chat", json={"message": "download fee defaulter report"})
print("Chat Response:", r2.json())

# 3. Extract download URL and try fetching the file
resp_text = r2.json()["data"]["response"]
import re
match = re.search(r'\]\((.*?)\)', resp_text)
if match:
    url = match.group(1)
    print("Downloading from:", url)
    if not url.startswith("http"):
        url = "http://localhost:5000" + url.split("?")[0]
    
    r3 = s.get(url)
    print("Download Status:", r3.status_code)
    print("File size:", len(r3.content), "bytes")
else:
    print("No download link found in response.")
