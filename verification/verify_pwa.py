from playwright.sync_api import sync_playwright

def verify_pwa():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the home page (assuming Flask runs on 5000)
        try:
            page.goto("http://127.0.0.1:5000", timeout=10000)
        except Exception as e:
            print(f"Failed to load page: {e}")
            return

        # 1. Verify manifest link exists
        manifest_link = page.locator("link[rel='manifest']")
        if manifest_link.count() > 0:
            print("SUCCESS: Manifest link found.")
            href = manifest_link.get_attribute("href")
            print(f"Manifest URL: {href}")

            # Fetch manifest content
            if href:
                response = page.request.get(href)
                if response.status == 200:
                    print("SUCCESS: Manifest file is accessible.")
                    print(response.json())
                else:
                    print(f"FAILURE: Manifest file returned status {response.status}")
        else:
            print("FAILURE: Manifest link NOT found.")

        # 2. Verify Service Worker registration script
        # We can check if the script text exists in the page source or if navigator.serviceWorker is accessed
        content = page.content()
        if "navigator.serviceWorker.register" in content:
            print("SUCCESS: Service Worker registration script found.")
        else:
            print("FAILURE: Service Worker registration script NOT found.")

        # 3. Verify SW file accessibility
        sw_response = page.request.get("http://127.0.0.1:5000/static/sw.js")
        if sw_response.status == 200:
            print("SUCCESS: sw.js file is accessible.")
        else:
             print(f"FAILURE: sw.js file returned status {sw_response.status}")

        # Take a screenshot just to be safe
        page.screenshot(path="verification/pwa_verification.png")
        browser.close()

if __name__ == "__main__":
    verify_pwa()
