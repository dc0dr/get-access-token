import logging

from login_bypass import login_bypass
from access_key_scraper import key_scraper
from file_uploader import upload_file

logging.basicConfig(
    level = logging.INFO,
    format = "%(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    p, context, page = login_bypass()

    if context is None:
        logger.exception("❌ Login bypass failed, exiting.....")
        return
    
    try:
        access_key = key_scraper(context, page)
        upload_file(access_key)
        logger.info("\n✅ Get-access-token script completed successfully")
    finally:
        # Clean up resources
        try:
            context.close()
            p.stop()
        except Exception as e:
            logger.exception("❌ Error during cleanup: %s", e)
    


if __name__ == "__main__":
    main()
