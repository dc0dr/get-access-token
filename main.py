import logging

from login_bypass import login_bypass

logging.basicConfig(
    level = logging.INFO,
    format = "%(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting the get-access-token script.....")
    login_bypass()
    logger.info("✅ Get-access-token script completed successfully")


if __name__ == "__main__":
    main()
