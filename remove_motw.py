import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def has_zone_identifier_ads(file_path: str) -> bool:
    """
    Checks if the Zone.Identifier alternate data stream (ADS) exists on the given file.

    Args:
        file_path (str): The full path to the file.

    Returns:
        bool: True if the Zone.Identifier ADS exists, False otherwise.
    """
    ads_path = file_path + ":Zone.Identifier"
    try:
        with open(ads_path, "r"):
            return True
    except FileNotFoundError:
        return False
    except OSError:
        # Could be a permissions issue or other I/O error
        return False


def remove_mark_of_the_web_from_shortcuts(desktop_path: str):
    """
    Removes the 'Mark of the Web' (Zone.Identifier ADS) from .url and .lnk
    files found in the user's Desktop folder. This function only targets
    the shortcut files themselves, not what they point to.

    Args:
        desktop_path (str): The full path to the user profile Desktop folder
                                 (e.g., 'C:\\Users\\YourUsername\\Desktop').
    """

    if not os.path.isdir(desktop_path):
        logger.info(f"Desktop folder not found for user profile: {desktop_path}")
        return

    logger.info(f"Starting Mark of the Web removal in: {desktop_path}")

    def _remove_ads(file_path: str):
        """
        Attempts to remove the Zone.Identifier ADS from a given file.
        Uses os.remove() first, then falls back to the native Windows 'del' command.
        """
        full_ads_path = file_path + ":Zone.Identifier"

        try:
            os.remove(full_ads_path)
            logger.info(f"  Successfully removed MotW from: {file_path} (via os.remove)")
        except FileNotFoundError:
            logger.info(f"  No Mark of the Web found for: {file_path}")
        except OSError as e:
            logger.info(f"  os.remove failed for {file_path}: {e}. Trying 'del' command.")
            try:
                command = f'cmd /c del /f /q "{full_ads_path}"'
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True
                )

                if result.returncode == 0:
                    if (
                        "Could not find" in result.stderr
                        or "File not found" in result.stderr
                    ):
                        logger.info(
                            f"  No Mark of the Web found for: {file_path} (confirmed by del command)."
                        )
                    else:
                        logger.info(
                            f"  Successfully removed MotW from: {file_path} (via del command)."
                        )
                else:
                    logger.error(
                        f"  Failed to remove MotW from {file_path}. Error: {result.stderr.strip()}"
                    )
            except Exception as sub_e:
                logger.error(f"  Subprocess error for {file_path}: {sub_e}")

    # Walk through the Desktop directory and its subfolders
    for root, _, files in os.walk(desktop_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            _, ext = os.path.splitext(file_name)
            ext = ext.lower()

            if ext in (".url", ".lnk"):
                if has_zone_identifier_ads(file_path):
                    logger.info(f"Processing shortcut with MotW: {file_name}")
                    _remove_ads(file_path)
                else:
                    logger.info(f"Skipping (no MotW): {file_name}")

    logger.info(f"Finished Mark of the Web removal for: {desktop_path}")
