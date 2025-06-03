import os
import subprocess
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


def quote_path(path: str) -> str:
    """
    Wraps a file path in double quotes to handle spaces and special characters.

    Args:
        path (str): The file or directory path to quote.

    Returns:
        str: The quoted path.
    """
    return f'"{path}"'


def build_robocopy_command(
    source: str,
    destination: str,
    base_options: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    exclude_files: Optional[List[str]] = None,
) -> List[str]:
    """
    Constructs a RoboCopy command list from parameters.

    Args:
        source (str): Source directory.
        destination (str): Destination directory.
        base_options (List[str], optional): Core options to apply.
        exclude_dirs (List[str], optional): Subdirectory names or paths to exclude.
        exclude_files (List[str], optional): File names or patterns to exclude.

    Returns:
        List[str]: A complete RoboCopy command suitable for subprocess.
    """
    cmd = ["robocopy", quote_path(source), quote_path(destination)]

    # Add base options safely
    if base_options:
        cmd.extend(base_options)

    # Add directory exclusions
    if exclude_dirs:
        cmd.append("/XD")
        cmd.extend(quote_path(d) for d in exclude_dirs)

    # Add file exclusions
    if exclude_files:
        cmd.append("/XF")
        cmd.extend(quote_path(f) for f in exclude_files)

    return cmd


def run_robocopy(
    ROBOCOPY_OPTIONS: List[str],
    source: str,
    destination: str,
    additional_options: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    exclude_files: Optional[List[str]] = None,
    dry_run: bool = False,
) -> int:
    """
    Executes RoboCopy from source to destination, applying given options.

    Args:
        source (str): Source directory (UNC or local).
        destination (str): Destination directory (local).
        additional_options (List[str], optional): RoboCopy switches beyond defaults.
        exclude_dirs (List[str], optional): Directory paths (relative to source) to exclude.
        exclude_files (List[str], optional): File patterns to exclude.
        dry_run (bool): If True, logs the command without executing.

    Returns:
        int: RoboCopy's exit code.
    """
    cmd = build_robocopy_command(
        source,
        destination,
        base_options=(ROBOCOPY_OPTIONS + (additional_options or [])),
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
    )

    logger.info(f"Running RoboCopy command:\n{' '.join(cmd)}")

    if dry_run:
        logger.info("[Dry Run] Command not executed.")
        return 0

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,  # Decode output as text
            bufsize=1,  # Line-buffered reading
        )
        # Stream each line as it comes in
        if process.stdout:
            for line in process.stdout:
                logger.info(line.rstrip())

        returncode = process.wait()
        logger.info(f"RoboCopy exited with code {returncode}")
        return returncode

    except Exception as e:
        logger.exception(f"Failed to execute RoboCopy: {e}")
        return -1


def robocopy_folder(
    ROBOCOPY_OPTIONS: List[str],
    source: str,
    destination: str,
    exclude_files: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    options: Optional[List[str]] = None,
    dry_run: bool = False,
) -> int:
    """
    Wrapper for RoboCopy with simplified interface for one folder.

    Args:
        source (str): Full source path.
        destination (str): Destination path.
        exclude_files (List[str], optional): Files to exclude.
        exclude_dirs (List[str], optional): Directories to exclude.
        options (List[str], optional): Extra RoboCopy options (default is empty list).
        dry_run (bool): If True, do not execute.

    Returns:
        int: RoboCopy exit code.
    """
    return run_robocopy(
        ROBOCOPY_OPTIONS,
        source=source,
        destination=destination,
        additional_options=options,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
        dry_run=dry_run,
    )


def copy_profile_root(
    ROBOCOPY_OPTIONS: List[str],
    source_root: str,
    dest_root: str,
    exclude_files: Optional[List[str]] = None,
    dry_run: bool = False,
):
    """
    Copies the root of a user's profile directory excluding AppData and sensitive files.

    Args:
        source_root (str): UNC path to the user profile root.
        dest_root (str): Local destination path.
        exclude_files (List[str], optional): Sensitive files to skip.
        dry_run (bool): If True, do not actually copy files.
    """
    logger.info("Copying user profile root (excluding AppData)...")
    robocopy_folder(
        ROBOCOPY_OPTIONS,
        source=source_root,
        destination=dest_root,
        exclude_dirs=["AppData"],
        exclude_files=exclude_files,
        dry_run=dry_run,
    )


def copy_appdata_subdirs(
    ROBOCOPY_OPTIONS: List[str],
    source_root: str,
    dest_root: str,
    subdirs: List[str],
    exclude_dirs: Optional[List[str]] = None,
    dry_run: bool = False,
):
    """
    Copies individual AppData subfolders in parallel using threads.

    Args:
        source_root (str): UNC path to profile root.
        dest_root (str): Local destination profile root.
        subdirs (List[str]): Relative paths to subfolders under AppData to include.
        exclude_dirs (List[str], optional): Folders to exclude from each subdir sync.
        dry_run (bool): If True, simulate only.
    """

    def copy_single_subdir(rel_path: str):
        src = os.path.join(source_root, rel_path)
        dst = os.path.join(dest_root, rel_path)

        if not dry_run:
            logger.info(f"[Thread] Creating AppData subfolder: {rel_path}")
            os.makedirs(dst, exist_ok=True)
        else:
            logger.info(f"[Thread] Skipping folder creation (dry run): {rel_path}")

        return robocopy_folder(
            ROBOCOPY_OPTIONS,
            source=src,
            destination=dst,
            exclude_dirs=exclude_dirs,
            dry_run=dry_run,
        )

    logger.info(f"Starting threaded copy of {len(subdirs)} AppData subfolders...")
    with ThreadPoolExecutor(max_workers=min(6, len(subdirs))) as executor:
        futures = {
            executor.submit(copy_single_subdir, subdir): subdir for subdir in subdirs
        }

        for future in as_completed(futures):
            subdir = futures[future]
            try:
                exit_code = future.result()
                logger.info(f"[Thread] Finished {subdir} with exit code {exit_code}")
            except Exception as e:
                logger.exception(f"[Thread] Error copying {subdir}: {e}")
