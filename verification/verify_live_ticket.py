from playwright.sync_api import sync_playwright
import time
from itsdangerous import URLSafeSerializer

def run():
    secret_key = 'tbib-secret-key-2024'
    s = URLSafeSerializer(secret_key)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Seed data
        print("Seeding data...")
        page.goto("http://127.0.0.1:5000/admin/seed_lite")
        time.sleep(2)

        # 2. Login as doctor to create a walkin
        print("Logging in...")
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='email']", "medecin1@tbib.dz")
        page.fill("input[name='password']", "123456")
        page.click("button[type='submit']")
        page.wait_for_url("http://127.0.0.1:5000/doctor/dashboard")
        print("Logged in!")

        # 3. Create a walk-in patient
        print("Creating walk-in...")
        page.evaluate("""
            fetch('/doctor/walkin', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'patient_name=TestLive&phone=0550001122&urgency_level=1'
            })
        """)
        time.sleep(2)

        # 4. Find the live ticket using token
        # We need to find the appointment ID first.
        # We'll try ID=1 which likely exists after seed + walkin.
        # We'll generate token for ID=1 and try to access it.
        # If not, try ID=2...

        found = False
        for i in range(1, 50):
            token = s.dumps(i)
            # Check if exists by hitting the status API
            resp = page.request.get(f"http://127.0.0.1:5000/patient/live/status/{token}")
            if resp.status == 200:
                print(f"Found appointment at ID {i} with token {token}")

                # Navigate to the live ticket page
                page.goto(f"http://127.0.0.1:5000/patient/live/{token}")

                # Wait for Alpine to render
                page.wait_for_selector(".circle-progress")

                # Verify content
                text = page.inner_text("body")
                if "Votre Ticket Live" in text:
                    print("Page verified!")
                    page.screenshot(path="verification/live_ticket_token.png")
                    found = True
                    break

        if not found:
            print("Could not find a valid appointment ID.")

        browser.close()

if __name__ == "__main__":
    run()
