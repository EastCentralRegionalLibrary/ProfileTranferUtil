import argparse
import os
import sys
import logging
from pathlib import Path
from unc_utils import check_unc_access, prompt_user_to_authenticate
from remove_motw import remove_mark_of_the_web_from_shortcuts
from robocopy_runner import copy_profile_root, copy_appdata_subdirs
from constants import (
    APPDATA_LOCAL_INCLUDE_DIRS,
    APPDATA_ROAMING_INCLUDE_DIRS,
    ROBOCOPY_EXCLUDE_FILES,
    ROBOCOPY_EXCLUDE_DIRS,
    USER_PROFILE_SUBPATH,
)

# Set up logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def build_unc_source(remote_machine: str, user_name: str) -> str:
    """
    Constructs the UNC path to the user's profile directory.
    """
    return rf"\\{remote_machine}\{USER_PROFILE_SUBPATH}\{user_name}"


def prompt_for_input(prompt_text: str, default: str = None) -> str:
    """
    Prompt the user for input with an optional default value.
    """
    if default:
        prompt_text += f" [{default}]"
    prompt_text += ": "
    response = input(prompt_text)
    return response.strip() or default


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments, falling back to interactive prompts if missing.
    """
    parser = argparse.ArgumentParser(
        description="Copy a user profile from a remote Windows machine using RoboCopy.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-m", "--machine", help="Remote machine name or IP address")
    parser.add_argument(
        "-u", "--username", help="Windows user name on the remote machine"
    )
    parser.add_argument(
        "-d", "--destination", help="Local destination path to copy data into"
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Simulate the copy operations without executing them",
    )
    return parser.parse_args()


def ensure_directory(path: str, dry_run: bool):
    """
    Create the destination directory if it doesn't exist.
    """
    if not dry_run:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Ensured destination directory exists: {path}")
    else:
        logger.info(f"Skipping destination directory creation: {path}")


def main():
    """
    Main CLI entry point for syncing a remote user profile to local storage using RoboCopy.
    Performs UNC access checks, profile copying, and post-processing.
    """
    args = parse_args()
    dry_run: bool = args.dryrun or False
    remote_machine = args.machine or prompt_for_input("Enter remote machine name or IP")
    user_name = args.username or prompt_for_input("Enter remote user name")
    destination = args.destination or prompt_for_input(
        "Enter destination path", default=str(Path.cwd())
    )

    if not remote_machine or not user_name:
        logger.error("Remote machine name and username are required.")
        sys.exit(1)

    unc_source = build_unc_source(remote_machine, user_name)
    logger.info(f"\nUNC source: {unc_source}")
    logger.info(f"Destination: {destination}\n")

    # Step 1: Verify UNC access or prompt authentication
    if not check_unc_access(unc_source):
        logger.warning("UNC path not accessible. Attempting authentication...")
        success = prompt_user_to_authenticate(rf"\\{remote_machine}\\C$")
        if not success or not check_unc_access(unc_source):
            logger.error("UNC path still inaccessible. Exiting.")
            sys.exit(1)

    # Step 2: Ensure destination exists
    ensure_directory(destination, dry_run)

    # Step 3: Confirm with user
    confirm = prompt_for_input("Proceed with sync? (y/n)", default="y")
    if confirm.lower() not in ("y", "yes"):
        logger.info("Operation cancelled by user.")
        sys.exit(0)

    # Step 4: Copy root profile data
    copy_profile_root(
        unc_source,
        destination,
        exclude_files=ROBOCOPY_EXCLUDE_FILES,
        dry_run=dry_run,
    )

    # Step 5: Copy AppData\Local subfolders
    copy_appdata_subdirs(
        unc_source,
        destination,
        APPDATA_LOCAL_INCLUDE_DIRS,
        exclude_dirs=ROBOCOPY_EXCLUDE_DIRS,
        dry_run=dry_run,
    )

    # Step 6: Copy AppData\Roaming subfolders
    copy_appdata_subdirs(
        unc_source,
        destination,
        APPDATA_ROAMING_INCLUDE_DIRS,
        dry_run=dry_run,
    )

    # Step 7: Post-processing (e.g., remove MotW)
    desktop_path = os.path.join(destination, "Desktop")
    logger.info(f"Removing MotW from shortcuts in: {desktop_path}")
    remove_mark_of_the_web_from_shortcuts(desktop_path)

    logger.info("Profile transfer complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()
