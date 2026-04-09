import os 
import shutil
import logging

logging.basicConfig(
    level = logging.INFO,
    format = '%(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def upload_file(file_content):
    """
    Creates the file that contains the access token and uploads it to the hardcoded OneDrive location on the user's PC

    Args:
        file_content: The access token to be written to the file
    """

    # Path relative to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output_files")
    os.makedirs(output_dir, exist_ok=True)
    
    file_dir = os.path.join(output_dir, "access_token.txt")
    logger.info(f"🔄 Creating file at {file_dir}.....\n")

    try:
        with open(file_dir, "w", encoding="utf-8") as file:
            file.write(file_content)
        logger.info("✅ Access token successfully written to file")
    except Exception as e:
        logger.exception("❌ File creation failed: %s", e)
        return None
    
