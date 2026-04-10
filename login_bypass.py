from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
from dotenv import load_dotenv
import logging
from typing import Any
from urllib.parse import urlparse

load_dotenv()
USER = os.environ["USER"]
USERNAME = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]
NAME = os.environ["NAME"]

logging.basicConfig(
    level = logging.INFO,
    format = '%(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def login_bypass() -> Any:
    profile_path = os.path.join(os.getcwd(), "browser_automation_profile")
    os.makedirs(profile_path, exist_ok=True)

    p = sync_playwright().start()

    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_path,
        channel="msedge",
        headless=False,
        args=["--start-maximized"],
        slow_mo=1500,
    )

    page = context.new_page()
    page.goto("https://developer.microsoft.com/en-us/graph/graph-explorer")
    logger.info("✅ Navigated to the Microsoft Graph Explorer page\n")

    try:
        with context.expect_page() as popup_info:
            page.get_by_role("button", name="Sign in").click()
        popup = popup_info.value
        parsed_init_url = urlparse(popup.url)
        logger.info("Popup opened at: %s://%s/", parsed_init_url.scheme, parsed_init_url.netloc)

        popup.wait_for_load_state("domcontentloaded", timeout=20000)

        for _ in range(10):
            parsed_url = urlparse(popup.url)
            current_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            logger.info("Popup opened at: %s", current_url)

            #Microsoft login page
            if "login.microsoftonline.com" in current_url:
                logger.info("➡️ Microsoft login page detected\n")
                handle_microsoft_login(popup, USERNAME)
                continue # in case of redirects, keep checking

            # OneLogin page
            elif "wvi.onelogin.com" in current_url:
                logger.info("➡️ OneLogin page detected\n")
                handle_onelogin_popup(popup, USERNAME, PASSWORD)
                break

            # Wait for a bit and recheck
            popup.wait_for_timeout(1500)
        else:
            logger.exception("❌ No known login page detected within timeout")
            return None, None, None

        # === Wait for popup to close (auth complete) ===
        try:
            popup.wait_for_event("close", timeout=60000)
            logger.info("✅ Login popup closed - returning to Graph Explorer!\n")
        except PlaywrightTimeoutError:
            logger.exception("⚠️ Popup did not close automatically....")

        # === Verify login succeeded ===
        try:
            #page.wait_for_selector(f"button[aria-label*='{NAME} Sign Out']", timeout=20000) //just realised it was deprecated after reading the docs
            login_verifier = page.locator(f"button[aria-label*='{NAME} Sign out' i]")
            login_verifier.wait_for(state="attached", timeout=20000)
            logger.info("✅ Successfully signed in to Graph Explorer!\n")
        except PlaywrightTimeoutError:
            logger.exception("⚠️ Could not confirm sign-in; check browser window manually!")

        # Return the Playwright instance, context, and page
        return p, context, page
            
    except Exception as e:
        logger.exception("❌ Login bypass failed: %s", e)
        
        # Clean up on error
        try:
            context.close()
            p.stop()
        except:
            pass
        return None, None, None




# ----- helper functions for each login type -----

def handle_microsoft_login(popup, username):
    """Handles Microsoft login sequence inside popup.

    Detects whichever of these 3 scenarios is present and handles it:
      1. Email input   — fresh login, need to type email
      2. Account picker — cached account tile to click
      3. Stay signed in — "Yes/No" prompt after auth
    """
    try:
        # Race all 3 possible selectors – whichever appears first wins
        email_sel = 'input[name="loginfmt"]'
        account_sel = f'[data-test-id="{username}"]'
        kmsi_sel = 'input[id="idBtn_Back"]'

        hit = popup.locator(f'{email_sel}, {account_sel}, {kmsi_sel}')
        hit.first.wait_for(state="visible", timeout=10000)

        # --- Scenario 1: email input (fresh login) ---
        if popup.locator(email_sel).is_visible():
            logger.info("  ↳ Email input detected – entering credentials")
            popup.fill(email_sel, username)
            popup.click('input[id="idSIButton9"]')
            popup.wait_for_timeout(2000)

        # --- Scenario 2: account picker ---
        if popup.locator(account_sel).is_visible():
            logger.info("  ↳ Account picker detected – selecting account")
            popup.locator(account_sel).click()
            popup.wait_for_timeout(2000)
        elif popup.get_by_label(username).is_visible():
            logger.info("  ↳ Account label detected – selecting account")
            popup.get_by_label(username).click()
            popup.wait_for_timeout(2000)

        # --- Scenario 3: "Stay signed in?" prompt ---
        try:
            popup.wait_for_selector(kmsi_sel, timeout=5000)
            logger.info("  ↳ 'Stay signed in?' prompt detected – clicking No")
            popup.click(kmsi_sel)
        except PlaywrightTimeoutError:
            pass

    except Exception as e:
        logger.exception("❌ Microsoft login failed: %s", e)
        return None, None, None


def handle_onelogin_popup(popup, username, password):
    """Handles OneLogin sequence inside popup"""
    
    try:
        popup.wait_for_selector("input[name='username']", timeout=15000)
        popup.fill("input[name='username']", username)
        popup.click("button[type='submit']")

        popup.wait_for_selector("input[name='password']", timeout=15000)
        popup.fill("input[name='password']", password)
        popup.click("button[type='submit']")
    except Exception as e:
        logger.exception("❌ OneLogin popup failed: %s", e)
        return None, None, None

        
    