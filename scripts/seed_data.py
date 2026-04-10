import requests
import json
import sys

BASE_URL = "http://localhost:5000/api"

def write_log(msg):
    with open("api_seed_report.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def test_login():
    url = f"{BASE_URL}/auth/login"
    payload = {"username": "superadmin", "password": "Admin@123"}
    try:
        resp = requests.post(url, json=payload)
        if resp.ok:
            token = resp.json()['data']['token']
            write_log("Login Successful")
            return token
        write_log(f"Login Failed: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        write_log(f"Login Exception: {e}")
    return None

def seed_data(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get College ID (assuming 1, but let's check or just use 1)
    college_id = 1

    # 2. Get Courses
    courses_resp = requests.get(f"{BASE_URL}/courses", headers=headers)
    if not courses_resp.ok:
        write_log("Failed to get courses")
        return
    courses = courses_resp.json()['data']
    if not courses:
        write_log("No courses found. Please add a course first.")
        return
    course_id = courses[0]['course_id']
    write_log(f"Using Course ID: {course_id} ({courses[0]['name']})")

    # 3. Add Batch
    batch_payload = {
        "college_id": college_id,
        "admission_year": 2026,
        "label": "2026-2030"
    }
    batch_resp = requests.post(f"{BASE_URL}/students/batches", json=batch_payload, headers=headers)
    if batch_resp.ok:
        batch_id = batch_resp.json()['data']['batch_id']
        write_log(f"Batch Created: {batch_id}")
    else:
        write_log(f"Batch Creation Failed: {batch_resp.text}")
        # Try to continue if batch exists? getting batches to find one
        batches_resp = requests.get(f"{BASE_URL}/students/batches", headers=headers)
        if batches_resp.ok and batches_resp.json()['data']:
            batch_id = batches_resp.json()['data'][0]['batch_id']
            write_log(f"Using Existing Batch: {batch_id}")
        else:
            return

    # 4. Add Section
    section_payload = {
        "batch_id": batch_id,
        "course_id": course_id,
        "name": "A",
        "current_semester": 1
    }
    section_resp = requests.post(f"{BASE_URL}/students/sections", json=section_payload, headers=headers)
    if section_resp.ok:
        section_id = section_resp.json()['data']['section_id']
        write_log(f"Section Created: {section_id}")
    else:
        write_log(f"Section Creation Failed: {section_resp.text}")

if __name__ == "__main__":
    with open("api_seed_report.txt", "w", encoding="utf-8") as f:
        f.write("API Seed Report\n")
    token = test_login()
    if token:
        seed_data(token)
