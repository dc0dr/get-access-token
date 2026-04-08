from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
from dotenv import load_dotenv
import logging
from typing import Any

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
        slow_mo=2000,
    )

    page = context.new_page()
    page.goto("https://developer.microsoft.com/en-us/graph/graph-explorer")
    logger.info("✅ Navigated to the Microsoft Graph Explorer page\n")

    try:
        with context.expect_page() as popup_info:
            page.get_by_role("button", name="Sign in").click()
        popup = popup_info.value
        logger.info("Popup opened at: %s", popup.url)

        popup.wait_for_load_state("domcontentloaded", timeout=20000)

        for _ in range(10):
            current_url = popup.url
            logger.info("Popup opened at: %s", current_url)

            #Microsoft login page
            if "login.microsoftonline.com" in current_url:
                logger.info("➡️ Microsoft login page detected\n")
                handle_microsoft_login(popup, USER)
                continue # in case of redirects, keep checking

            # OneLogin page
            elif "wvi.onelogin.com" in current_url:
                logger.info("➡️ OneLogin page detected\n")
                handle_onelogin_popup(popup, USERNAME, PASSWORD)

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
            page.wait_for_selector(f"button[aria-label*='{NAME} Sign Out']", timeout=2000)
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
    """Handles Microsoft login sequence inside popup"""
    try:
        popup.get_by_label(username).click()

        # Handle 'Stay signed in?' if it appears
        try:
            popup.wait_for_selector('input[id="idBtn_Back"]', timeout=5000)
            popup.click('input[id="idBtn_Back"]')
        except PlaywrightTimeoutError:
            pass
    except Exception as e:
        logger.exception("❌ Microsoft login failed: %s", e)
        return None, None, None


def handle_onelogin_popup(popup, username, password):
    """Handles OneLogin sequence inside popup"""
    
    try:
        popup.wait_for_selector("input[name='username']", timeout=20000)
        popup.fill("input[name='username']", username)
        popup.click("button[type='submit']")

        popup.wait_for_selector("input[name='password']", timeout=20000)
        popup.fill("input[name='password']", password)
        popup.click("button[type='submit']")
    except Exception as e:
        logger.exception("❌ OneLogin popup failed: %s", e)
        return None, None, None

        
    