import os
import subprocess
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_regexport(
    source: str,
    destination_file: str,
    dry_run: bool = False,
) -> int:
    """
    Executes the 'reg export' command to export a specified registry key
    to a destination .reg file.

    Args:
        source (str): The full path to the registry key or hive to export (e.g.,
            "HKEY_CURRENT_USER\\Software\\Microsoft").
        destination_file (str): The full path to the .reg file where the export
                                will be saved.
        dry_run (bool): If True, the command will be logged but not executed.

    Returns:
        int: The exit code of the 'reg export' command, or -1 if an exception occurs.
    """
    # Construct the command for reg export
    # Note: Using shell=True for simplicity with 'reg' command on Windows.
    # Be cautious if 'source' or 'destination_file' come from untrusted input.
    cmd = f'reg export "{source}" "{destination_file}" /y'  # /y to overwrite without prompt

    if dry_run:
        logger.info(f"[Dry Run] Command: '{cmd}' (not executed).")
        return 0

    logger.info(f"Executing command: '{cmd}'")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout for unified logging
            text=True,  # Decode output as text
            bufsize=1,  # Line-buffered reading for real-time output
            shell=True,  # Execute command via system shell
        )

        # Stream each line of output as it comes in
        if process.stdout:
            for line in process.stdout:
                logger.info(f"Output for '{source}': {line.rstrip()}")

        returncode = process.wait()  # Wait for the process to complete
        logger.info(
            f"'{source}' (exported to '{os.path.basename(destination_file)}') exited with code {returncode}"
        )
        return returncode

    except Exception as e:
        logger.exception(f"Failed to execute 'reg export' for '{source}': {e}")
        return -1


def reg_export(
    src: List[str],
    dst_directory: str,  # Renamed to clarify it's a directory
    dry_run: bool = False,
):
    """
    Exports multiple registry keys concurrently to separate .reg files
    within a specified destination directory.

    Args:
        src (List[str]): A list of full paths to the registry keys or hives
            to export (e.g., ["HKEY_CURRENT_USER\\Software", "HKEY_LOCAL_MACHINE\\SYSTEM"]).
        dst_directory (str): The path to the directory where the exported .reg files
            will be saved. Each export will create a unique file here.
        dry_run (bool): If True, commands will be logged but not executed.
    """

    # Ensure the destination directory exists
    os.makedirs(dst_directory, exist_ok=True)
    logger.info(f"Ensured destination directory exists: {dst_directory}")

    def export_single_path(single_path: str):
        """
        Helper function to export a single registry path.
        Generates a unique filename for each export.
        """
        # Create a safe filename from the registry path
        # Replace forbidden characters with underscores and append .reg
        base_name = (
            single_path.replace("HKEY_", "")
            .replace("\\", "_")
            .replace("/", "_")
            .replace(":", "_")
            .replace(" ", "_")
        )
        destination_file = os.path.join(dst_directory, f"{base_name}.reg")

        logger.info(f"Exporting '{single_path}' to '{destination_file}'...")
        return run_regexport(
            source=single_path,
            destination_file=destination_file,
            dry_run=dry_run,
        )

    logger.info("Starting concurrent export of registry items...")
    # Determine the number of worker threads (min 6 or number of items)
    max_workers = (
        min(6, len(src)) if src else 1
    )  # Ensure at least 1 worker if src is empty

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks to the thread pool, mapping future objects to their source paths
        futures = {executor.submit(export_single_path, entry): entry for entry in src}

        # Iterate over completed futures as they finish
        for future in as_completed(futures):
            entry = futures[
                future
            ]  # Get the original source path for the completed future
            try:
                exit_code = (
                    future.result()
                )  # Retrieve the result (exit code) of the task
                logger.info(
                    f"[Thread] Finished exporting '{entry}' with exit code {exit_code}"
                )
            except Exception as e:
                # Log any exceptions that occurred during the execution of a task
                logger.exception(f"[Thread] Error exporting '{entry}': {e}")

    logger.info("Finished all registry export operations.")


# Example Usage (uncomment to test)
# if __name__ == "__main__":
#     # Define some registry paths to export
#     registry_paths_to_export = [
#         "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
#         "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer",
#         "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment"
#     ]

#     # Define the destination directory for the .reg files
#     output_directory = "C:\\RegExports" # IMPORTANT: Choose a directory where you have write permissions

#     # Run the export (set dry_run=True to test without actual export)
#     reg_export(
#         src=registry_paths_to_export,
#         dst_directory=output_directory,
#         dry_run=False  # Set to True for a dry run, False for actual export
#     )
