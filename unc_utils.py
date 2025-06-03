"""
unc_utils.py

Utilities for working with UNC (Universal Naming Convention) paths,
including access checks and authentication prompts using Windows Explorer.
"""

import os
import time
import logging

logger = logging.getLogger(__name__)


def check_unc_access(unc_path: str) -> bool:
    """
    Check whether the given UNC path is accessible.

    Args:
        unc_path (str): A UNC path, e.g., \\\\RemotePC\\C$\\Users\\SomeUser

    Returns:
        bool: True if the path exists and is accessible, False otherwise.
    """
    return os.path.exists(unc_path)


def prompt_user_to_authenticate(
    unc_root: str, timeout: int = 120, interval: float = 2.0
) -> bool:
    """
    Opens a UNC path in Windows Explorer to prompt authentication
    and waits until the path becomes accessible.

    Args:
        unc_root (str): The root UNC path to open (e.g., \\\\RemotePC\\C$)
        timeout (int): Maximum time in seconds to wait for authentication
        interval (float): Seconds to wait between access checks

    Returns:
        bool: True if the path became accessible within the timeout,
              False otherwise.
    """
    logger.info(f"Launching Windows Explorer to authenticate UNC path:\n  {unc_root}")

    try:
        os.startfile(unc_root)
    except Exception as e:
        logger.error(f"Failed to open UNC path: {e}")
        return False

    logger.info(f"Waiting for UNC access (timeout = {timeout}s)...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(unc_root):
            print("Access to UNC path confirmed.")
            return True
        time.sleep(interval)

    logger.error("Timeout reached. UNC path is still inaccessible.")
    return False
