from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
from dotenv import load_dotenv
import logging
from typing import Any
from urllib.parse import urlparse

# overrides env vars if already loaded to prevent stale values and reflect changes in the .env file
# Without override=True, if .env was changed after the script started, the script would keep using the old values
load_dotenv(override=True)


USER_LOCATOR = os.environ["USER_LOCATOR"]
USERNAME = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]
NAME = os.environ["NAME"]

logging.basicConfig(
    level = logging.INFO,
    format = '%(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def login_bypass() -> Any:
    project_root = os.path.dirname(os.path.abspath(__file__))
    profile_path = os.path.join(project_root, "browser_automation_profile")
    os.makedirs(profile_path, exist_ok=True)

    p = sync_playwright().start()

    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_path,
        channel="msedge",
        headless=True,
        args=["--start-maximized"],
        slow_mo=1500,
    )

    page = context.new_page()
    page.goto("https://developer.microsoft.com/en-us/graph/graph-explorer")
    logger.info("✅ Navigated to the Microsoft Graph Explorer page\n")

    try:
        login_verifier = page.locator(f"button[aria-label*='{NAME} Sign out' i]")
        sign_in_btn = page.get_by_role("button", name="Sign in")

        # Wait for either the Sign in button or the signed-in user button to appear
        sign_in_btn.or_(login_verifier).first.wait_for(state="visible", timeout=20000)

        if login_verifier.is_visible():
            logger.info("✅ Already signed in to Graph Explorer!\n")
            return p, context, page

        popup = None
        try:
            with context.expect_page(timeout=15000) as popup_info:
                sign_in_btn.click()
            popup = popup_info.value
        except PlaywrightTimeoutError:
            # Silent SSO / cached session may sign in without opening a popup
            try:
                login_verifier.wait_for(state="attached", timeout=5000)
                logger.info("✅ Signed in silently to Graph Explorer (no popup)!\n")
                return p, context, page
            except PlaywrightTimeoutError:
                raise PlaywrightTimeoutError(
                    "No login popup opened and sign-in did not complete within timeout"
                )

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
    """Handles OneLogin sequence inside popup.

    Supports both fresh logins (username then password) and remembered sessions
    where OneLogin skips straight to the password prompt.
    """
    username_sel = "input[name='username']"
    password_sel = "input[name='password']"
    submit_sel = "button[type='submit']"

    try:
        # Wait for either visible username (fresh login) or visible password (remembered user).
        # :visible avoids matching the hidden <input hidden name="username"> on remembered sessions.
        popup.locator(f"{username_sel}:visible, {password_sel}:visible").first.wait_for(
            state="visible", timeout=15000
        )

        if popup.locator(username_sel).is_visible():
            logger.info("  ↳ OneLogin username input detected – entering username")
            popup.fill(username_sel, username)
            if not popup.locator(password_sel).is_visible():
                popup.click(submit_sel)

        password_input = popup.locator(password_sel)
        password_input.wait_for(state="visible", timeout=15000)
        logger.info("  ↳ OneLogin password input detected – entering password")
        password_input.fill(password)
        popup.click(submit_sel)
    except Exception as e:
        logger.exception("❌ OneLogin popup failed: %s", e)
        return None, None, None

        
    