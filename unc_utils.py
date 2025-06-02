"""
unc_utils.py

Utilities for working with UNC (Universal Naming Convention) paths,
including access checks and authentication prompts using Windows Explorer.
"""

import os
import subprocess
import time


def check_unc_access(unc_path: str) -> bool:
    """
    Check whether the given UNC path is accessible.

    Args:
        unc_path (str): A UNC path, e.g., \\\\RemotePC\\C$\\Users\\SomeUser

    Returns:
        bool: True if the path exists and is accessible, False otherwise.
    """
    return os.path.exists(unc_path)


def prompt_user_to_authenticate(unc_root: str, timeout: int = 120) -> bool:
    """
    Opens a UNC path in Windows Explorer to prompt authentication
    and waits for the user to close the window.

    Args:
        unc_root (str): The root UNC path to open (e.g., \\\\RemotePC\\C$)
        timeout (int): Maximum time in seconds to wait for user to close Explorer.

    Returns:
        bool: True if the user closed the Explorer window within the timeout,
              False if the timeout was reached or if Explorer failed to launch.
    """
    print(f"Launching Windows Explorer to authenticate UNC path:\n  {unc_root}")

    try:
        # Start Explorer and monitor process
        proc = subprocess.Popen(["explorer", unc_root], shell=False)

        print(f"Waiting for the Explorer window to be closed (timeout = {timeout}s)...")

        start_time = time.time()
        while True:
            if proc.poll() is not None:
                print("Explorer window closed.")
                return True

            if time.time() - start_time >= timeout:
                print(
                    "Timeout reached. Proceeding without confirmation of authentication."
                )
                return False

            time.sleep(1)

    except Exception as e:
        print(f"Failed to launch Explorer: {e}")
        return False
