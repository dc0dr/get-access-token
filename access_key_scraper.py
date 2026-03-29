from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def key_scraper(context, page) -> None:
    """
    Scrapes the access key from the Workfront login page.
    
    Args:
        context: Playwright context
        page: Playwright page
    
    Returns:
        None
    
    Raises:
        PlaywrightTimeoutError: If the page times out
    """

    logger.info("🔄 Starting the access key scraper.....\n")
    try:
        page.get_by_role("button", name="Run query").click()
        
    except Exception as e:
        logger.exception("❌ Error: %s", e)
        return None
    