from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
from dotenv import load_dotenv
import logging
from typing import Any

load_dotenv()
USER = os.environ["USER"]
USERNAME = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]

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
    except Exception as e:
        logger.exception("❌ Login bypass failed: %s", e)
        
        # Clean up on error
        try:
            context.close()
            p.stop()
        except:
            pass
        return None, None, None