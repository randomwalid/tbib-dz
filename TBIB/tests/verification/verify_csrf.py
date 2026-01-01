
from playwright.sync_api import sync_playwright, expect
import time
import os

def verify_csrf_fix():
    # Ensure screenshots directory exists
    screenshot_dir = "tests/verification/screenshots"
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        base_url = "http://127.0.0.1:5001"

        print(f"Connecting to {base_url}...")
        try:
            page.goto(f"{base_url}/register")
        except Exception as e:
            print(f"Failed to connect to {base_url}. Trying port 5000...")
            base_url = "http://127.0.0.1:5000"
            page.goto(f"{base_url}/register")

        # 1. Register Patient
        email = f"test_patient_{int(time.time())}@example.com"
        print(f"Registering user: {email}")

        page.fill('input[name="name"]', "Test Patient")
        page.fill('input[name="email"]', email)
        page.fill('input[name="phone"]', "0555123456")
        page.fill('input[name="password"]', "password123")

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        print(f"Current URL after register: {page.url}")

        # 2. Go to Profile and Verify CSRF
        print("Navigating to profile...")
        page.goto(f"{base_url}/patient/profile")

        forms_with_csrf = page.locator('form input[name="csrf_token"]')
        count = forms_with_csrf.count()
        print(f"Found {count} forms with CSRF token on Profile page.")

        # Debug: Print form actions
        forms = page.locator('form').all()
        print(f"DEBUG: Found {len(forms)} total forms on page.")
        for i, form in enumerate(forms):
            action = form.get_attribute('action') or "(No Action)"
            has_csrf = form.locator('input[name="csrf_token"]').count() > 0
            print(f"Form {i+1}: Action='{action}', Has CSRF={has_csrf}")

        if count >= 4:
            print("✅ SUCCESS: Found at least 4 forms with CSRF tokens.")
        else:
            print(f"❌ FAILURE: Expected at least 4 CSRF tokens, found {count}")

        page.screenshot(path=f"{screenshot_dir}/patient_profile_csrf.png")

        # 3. Doctor Login Check
        print("Logging out patient...")
        page.goto(f"{base_url}/logout")

        print("Logging in as doctor...")
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "doctor1@tbib.dz")
        page.fill('input[name="password"]', "doctor123")
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        print(f"Current URL after doctor login: {page.url}")

        if "/doctor/dashboard" in page.url:
            print("✅ Doctor Login Successful")

            # Check for fetch fix in source
            content = page.content()
            if "'X-CSRFToken':" in content:
                 print("✅ SUCCESS: Found 'X-CSRFToken' header in Doctor Dashboard.")
            else:
                 print("❌ FAILURE: 'X-CSRFToken' header NOT found in Doctor Dashboard.")

            page.screenshot(path=f"{screenshot_dir}/doctor_dashboard.png")

        else:
             print("❌ Doctor Login Failed")
             if "Email ou mot de passe incorrect" in page.content():
                 print("Reason: Invalid Credentials")
             else:
                 print("Reason: Unknown (Check screenshot)")
             page.screenshot(path=f"{screenshot_dir}/doctor_login_fail.png")

        browser.close()

if __name__ == "__main__":
    verify_csrf_fix()
