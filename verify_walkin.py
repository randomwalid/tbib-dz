import time
import os
import subprocess
import sys
from playwright.sync_api import sync_playwright

def verify_walkin():
    # Start Flask App in background using uv run FROM TBIB DIRECTORY
    print("Starting Flask server...")
    server = subprocess.Popen(
        ["uv", "run", "python", "main.py"],
        cwd="TBIB",  # Important: execute in the project directory
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start
    print("Waiting for server to initialize...")
    time.sleep(10)

    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 720})
            page = context.new_page()

            # 1. Login
            print("Navigating to login...")
            try:
                page.goto("http://127.0.0.1:5000/login", timeout=30000)
            except Exception as e:
                print(f"Failed to load login page: {e}")
                # Check server output immediately
                if server.poll() is not None:
                     out, err = server.communicate()
                     print("Server crashed early:")
                     print(err)
                raise e

            print("Logging in as doctor...")
            # Use 'doc@tbib.dz' / 'doc' from seed_test_accounts
            page.fill("input[name='email']", "doc@tbib.dz")
            page.fill("input[name='password']", "doc")
            page.click("button[type='submit']")

            page.wait_for_url("**/doctor/dashboard")
            print("Logged in successfully.")

            # 2. Open Walk-in Modal
            print("Opening Walk-in modal...")
            page.click("button:has-text('Urgence / Walk-in')")

            # Wait for modal visibility
            page.wait_for_selector("form[action='/doctor/walkin']")

            # 3. Fill Form
            print("Filling Walk-in form...")
            page.fill("input[name='patient_name']", "Test Patient Walkin")
            # Leave phone empty to test the fix

            # 4. Submit
            print("Submitting form...")
            page.click("form[action='/doctor/walkin'] button[type='submit']")

            # 5. Wait for result
            # It redirects to dashboard and shows a flash message
            print("Waiting for redirection/result...")
            page.wait_for_url("**/doctor/dashboard")

            # Wait for flash message text specifically
            print("Waiting for success message...")
            page.wait_for_selector("text=Patient Test Patient Walkin ajouté", timeout=10000)

            # 6. Screenshot
            print("Taking screenshot...")
            page.screenshot(path="debug_walkin_success.png")
            print("Screenshot saved to debug_walkin_success.png")

            print("VERIFICATION SUCCESSFUL!")

            browser.close()

    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
        # Capture stdout/stderr from server if failed
        try:
             server.terminate()
             out, err = server.communicate(timeout=5)
             print("--- Server STDOUT ---")
             print(out)
             print("--- Server STDERR ---")
             print(err)
        except:
             pass
        raise e
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait()

if __name__ == "__main__":
    verify_walkin()
