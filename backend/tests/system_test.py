import re
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # Launch browser
        print("Launching browser...")
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Define Base URL - Adjust if needed
            BASE_URL = "http://localhost/management-system/Main/Frontend"
            
            print(f"Testing against: {BASE_URL}")

            # 1. Login
            print("\n--- TEST: Login ---")
            try:
                page.goto(f"{BASE_URL}/login.html")
                page.fill('#username', 'superadmin')
                page.fill('#password', 'Admin@123')
                
                # Check for response
                with page.expect_response("**/api/auth/login") as response_info:
                    page.click('#login-btn')
                
                response = response_info.value
                if response.status == 200:
                    print("Login API hit successful.")
                else:
                    print(f"Login API returned status: {response.status}")
                
                # Wait for navigation to dashboard
                page.wait_for_url(f"**/dashboard.html")
                print("Login: SUCCESS - Redirected to Dashboard")
            except Exception as e:
                print(f"Login: FAILED - {str(e)}")
                browser.close()
                return

            # 2. Test Modules
            modules = [
                {"name": "Dashboard", "path": "dashboard.html"},
                {"name": "Students", "path": "students/index.html"},
                {"name": "Staff", "path": "staff/index.html"},
                {"name": "Departments", "path": "departments/index.html"},
                {"name": "Courses", "path": "courses/index.html"},
                {"name": "Timetable", "path": "timetable/index.html"},
                {"name": "Attendance", "path": "attendance/index.html"},
                {"name": "Marks", "path": "marks/index.html"},
                {"name": "Fees", "path": "fees/index.html"},
                {"name": "Reports", "path": "reports/index.html"},
                {"name": "Notifications", "path": "notifications/index.html"},
                {"name": "Settings", "path": "settings/index.html"}
            ]

            print("\n--- TEST: Navigation & Page Errors ---")
            
            for mod in modules:
                url = f"{BASE_URL}/{mod['path']}"
                print(f"Testing {mod['name']}...", end=" ")
                
                errors = []
                page.on("console", lambda msg: errors.append(f"Console: {msg.text}") if msg.type == "error" else None)
                page.on("pageerror", lambda exc: errors.append(f"PageError: {exc}"))

                try:
                    response = page.goto(url)
                    page.wait_for_load_state("networkidle") # Wait for API calls to likely finish
                    
                    if response.status >= 400:
                        errors.append(f"HTTP Error: {response.status}")
                    
                    # Check for common UI error indicators
                    if page.locator(".toast-error").is_visible():
                        errors.append("UI Error Toast detected")
                    if page.get_by_text("Failed to fetch").is_visible():
                        errors.append("UI Error: 'Failed to fetch' visible")

                    if not errors:
                        print("SUCCESS")
                    else:
                        print(f"FAILED")
                        for err in errors:
                            print(f"  - {err}")
                            
                except Exception as e:
                    print(f"FAILED (Exception: {str(e)})")
                
                # Remove listeners to avoid duplicates
                page.remove_listener("console", lambda: None) # crude, but strictly listeners are added per page object instance persistence? 
                # Actually in playwright python listeners are cumulative if not removed.
                # Better to recreate page or context? No, just clearing errors list is fine for reporting, 
                # but listeners will pile up.
                # Let's just create a new list per loop and accept we might get some dupes if we don't clear.
                # To clear all console listeners:
                page.remove_listener("console", page.listeners("console")[0]) if page.listeners("console") else None
                page.remove_listener("pageerror", page.listeners("pageerror")[0]) if page.listeners("pageerror") else None

            browser.close()
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    run()
