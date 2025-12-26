from playwright.sync_api import sync_playwright, expect
import time

def verify_landing_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Desktop View
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.goto("http://127.0.0.1:5000/")

        # Wait for loader to disappear
        page.wait_for_selector("#globalLoader", state="hidden", timeout=10000)

        # Verify Hero Section Elements
        expect(page.get_by_role("heading", name="Votre santé, simplifiée.")).to_be_visible()
        expect(page.get_by_text("Trouvez le bon médecin et prenez rendez-vous en ligne.")).to_be_visible()

        # Verify Logo (specific one)
        logo = page.locator("img[src*='logo_accueil_transparent.png']")
        expect(logo).to_be_visible()

        # Verify Search Form
        expect(page.get_by_role("button", name="Rechercher")).to_be_visible()

        # Verify Legal Links
        expect(page.get_by_role("link", name="Conditions Générales")).to_be_visible()
        expect(page.get_by_role("link", name="Confidentialité (Loi 18-07)")).to_be_visible()

        # Screenshot Desktop
        page.screenshot(path="/home/jules/verification/landing_desktop.png")
        print("Desktop screenshot taken.")

        # 2. Mobile View
        context_mobile = browser.new_context(
            viewport={'width': 375, 'height': 812},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
        )
        page_mobile = context_mobile.new_page()
        page_mobile.goto("http://127.0.0.1:5000/")

        # Wait for loader
        page_mobile.wait_for_selector("#globalLoader", state="hidden", timeout=10000)

        # Screenshot Mobile
        page_mobile.screenshot(path="/home/jules/verification/landing_mobile.png")
        print("Mobile screenshot taken.")

        # 3. Verify CGU Page
        page.goto("http://127.0.0.1:5000/legal/cgu")
        page.wait_for_selector("#globalLoader", state="hidden", timeout=10000)
        expect(page.get_by_text("Juridiction & Droit Applicable")).to_be_visible()
        expect(page.get_by_text("Conformité Ordinal")).to_be_visible()
        page.screenshot(path="/home/jules/verification/cgu.png")
        print("CGU screenshot taken.")

        # 4. Verify Privacy Page
        page.goto("http://127.0.0.1:5000/legal/privacy")
        page.wait_for_selector("#globalLoader", state="hidden", timeout=10000)
        expect(page.get_by_text("Hébergement Souverain (Loi 18-07)")).to_be_visible()
        expect(page.get_by_text("Partage de Données")).to_be_visible()
        page.screenshot(path="/home/jules/verification/privacy.png")
        print("Privacy screenshot taken.")

        browser.close()

if __name__ == "__main__":
    verify_landing_page()
