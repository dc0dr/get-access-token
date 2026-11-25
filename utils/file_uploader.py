import os 
import shutil
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

DESTINATION_DIR = os.environ["DESTINATION_DIR"]

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
    
    file_path = os.path.join(output_dir, "access_token.txt")
    logger.info(f"🔄 Creating file at {file_path}.....\n")

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(file_content)
        logger.info("✅ Access token successfully written to file")
    except Exception as e:
        logger.exception("❌ File creation failed: %s", e)
        return None

    # ---- Copy the file to the OneDrive folder -------

    destination_dir = DESTINATION_DIR
    os.makedirs(destination_dir, exist_ok=True)
    destination_file = os.path.join(destination_dir, os.path.basename(file_path))

    try:
        # Remove any existing file first to avoid in-place overwrite issues on OneDrive/CloudStorage
        if os.path.lexists(destination_file):
            os.remove(destination_file)

        destination_path = shutil.copy(file_path, destination_file)
        logger.info("✅ File copied to: %s", destination_path)
    except PermissionError as e:
        logger.exception(
            "❌ Permission denied copying to %s (check macOS Full Disk Access / OneDrive permissions): %s",
            destination_file,
            e,
        )
        return None
    except Exception as e:
        logger.exception("❌ Failed to copy file to %s: %s", destination_file, e)
        return None

    # ---- Deletes the original file (only if copying succeeded) ----
    if os.path.exists(destination_path):
        os.remove(file_path)
        logger.info("✅ Original file deleted: %s", file_path)
    else:
        logger.error("❌ Destination file not found after copy: %s", destination_path)
        return None
    
    

    
