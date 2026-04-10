from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def key_scraper(context, page) -> None:
    """
    Scrapes the access key from the Workfront login page.
    
    Args:
        context: The Playwright browser context from login_bypass
        page: The active page from login_bypass
    
    Returns:
        None
    
    Raises:
        PlaywrightTimeoutError: If the page times out
    """

    logger.info("🔄 Starting the access key scraper.....\n")
    try:
        page.get_by_role("button", name="Run query").click()
        logger.info("Query button exists. ✅ Clicked the run query button....")
        page.get_by_role("tab", name="Access token").click()
        logger.info("Access token tab exists. ✅ Clicked the access token tab....")
        access_key = page.locator("id=access-token").inner_text()
        logger.info("✅ Access token successfully obtained\n")
        
        return access_key
        
    except Exception as e:
        logger.exception("❌ Access key scraper failed: %s", e)
        return None
    