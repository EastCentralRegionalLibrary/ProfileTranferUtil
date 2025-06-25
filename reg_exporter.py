import os
import subprocess
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logger = logging.getLogger(__name__)


def find_executable(executable_name: str) -> Optional[str]:
    """
    Searches for an executable in the system's PATH.

    Args:
        executable_name (str): The name of the executable (e.g., "psexec.exe").

    Returns:
        Optional[str]: The full path to the executable if found, otherwise None.
    """
    # Check if the executable is in the current working directory
    if os.path.exists(executable_name) and os.path.isfile(executable_name):
        logger.info(
            f"Found '{executable_name}' in current directory: {os.path.abspath(executable_name)}"
        )
        return os.path.abspath(executable_name)

    # Search in system PATH
    for path in os.environ["PATH"].split(os.pathsep):
        full_path = os.path.join(path, executable_name)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            logger.info(f"Found '{executable_name}' in PATH: {full_path}")
            return full_path
    logger.warning(
        f"Executable '{executable_name}' not found in PATH or current directory."
    )
    return None


def run_regexport(
    source: str,
    destination_file: str,
    dry_run: bool = False,
    psexec_path: Optional[str] = None,
) -> int:
    """
    Executes the 'reg export' command to export a specified registry key
    to a destination .reg file, optionally using PsExec.

    Args:
        source (str): The full path to the registry key or hive to export (e.g.,
            "HKEY_CURRENT_USER\\Software\\Microsoft").
        destination_file (str): The full path to the .reg file where the export
                                 will be saved.
        dry_run (bool): If True, the command will be logged but not executed.
        psexec_path (Optional[str]): The full path to the PsExec.exe executable.
                                     If provided, PsExec will be used to run the command
                                     as the logged-in user (session 1).

    Returns:
        int: The exit code of the command, or -1 if an exception occurs.
    """
    # Construct the base 'reg export' command
    reg_cmd = f'reg export "{source}" "{destination_file}" /y'

    # If psexec_path is provided, prepend PsExec command
    if psexec_path:
        # Use -i 1 for interactive session 1, and -h to run with elevated privileges
        # Enclose the reg_cmd in quotes to pass it as a single argument to PsExec
        cmd = f'"{psexec_path}" -i 1 -h cmd /c "{reg_cmd}"'
        logger.info(f"Using PsExec: {psexec_path}")
    else:
        cmd = reg_cmd
        logger.info("Not using PsExec.")

    if dry_run:
        logger.info(f"[Dry Run] Command: '{cmd}' (not executed).")
        return 0

    logger.info(f"Executing command: '{cmd}'")
    try:
        # Use shell=True for simpler command execution, especially with complex quoting
        # when PsExec is involved. Be cautious with untrusted input for 'source'/'destination_file'.
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

    except FileNotFoundError:
        logger.error(
            f"Command or PsExec executable not found. Ensure PsExec is in PATH or specified correctly: {cmd}"
        )
        return -1
    except Exception as e:
        logger.exception(f"Failed to execute command for '{source}': {e}")
        return -1


def reg_export(
    src: List[str],
    dst_directory: str,
    use_psexec: bool = True,
    dry_run: bool = False,
    psexec_custom_path: Optional[str] = None,
):
    """
    Exports multiple registry keys concurrently to separate .reg files
    within a specified destination directory, optionally using PsExec.

    Args:
        src (List[str]): A list of full paths to the registry keys or hives
            to export (e.g., ["HKEY_CURRENT_USER\\Software", "HKEY_LOCAL_MACHINE\\SYSTEM"]).
        dst_directory (str): The path to the directory where the exported .reg files
            will be saved. Each export will create a unique file here.
        dry_run (bool): If True, commands will be logged but not executed.
        use_psexec (bool): If True, PsExec will be used to run the 'reg export' commands.
        psexec_custom_path (Optional[str]): A custom path to PsExec.exe if it's not
                                             in the system PATH.
    """

    psexec_executable_path = None
    if use_psexec:
        if psexec_custom_path:
            psexec_executable_path = psexec_custom_path
            if not (
                os.path.exists(psexec_executable_path)
                and os.path.isfile(psexec_executable_path)
            ):
                logger.critical(
                    f"PsExec executable not found at specified custom path: {psexec_custom_path}"
                )
                return
        else:
            psexec_executable_path = find_executable("PsExec.exe")
            if not psexec_executable_path:
                logger.critical(
                    "PsExec.exe not found in system PATH or current directory. "
                    "Please add it to PATH or provide 'psexec_custom_path'."
                )
                return

    # Ensure the destination directory exists
    dest = os.path.normpath(dst_directory)
    os.makedirs(dest, exist_ok=True)
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
            psexec_path=psexec_executable_path,
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
            finished_entry = futures[
                future
            ]  # Get the original source path for the completed future
            try:
                exit_code = (
                    future.result()
                )  # Retrieve the result (exit code) of the task
                logger.info(
                    f"[Thread] Finished exporting '{finished_entry}' with exit code {exit_code}"
                )
            except Exception as e:
                # Log any exceptions that occurred during the execution of a task
                logger.exception(f"[Thread] Error exporting '{finished_entry}': {e}")

    logger.info("Finished all registry export operations.")


# # Example Usage (uncomment to test)
# if __name__ == "__main__":
#     # Define some registry paths to export
#     registry_paths_to_export = [
#         "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
#         "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer",
#         "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment",
#     ]

#     # Define the destination directory for the .reg files
#     # IMPORTANT: Choose a directory where you have write permissions
#     output_directory = "C:\\RegExports"

#     # --- Example 1: Dry run without PsExec ---
#     logger.info("\n--- Running Dry Run (no PsExec) ---")
#     reg_export(
#         src=registry_paths_to_export,
#         dst_directory=output_directory,
#         dry_run=True,
#         use_psexec=False,
#     )

#     # --- Example 2: Actual export using PsExec (if found) ---
#     logger.info(
#         "\n--- Attempting Actual Export with PsExec (requires PsExec.exe in PATH or custom path) ---"
#     )
#     # You can set psexec_custom_path if PsExec.exe is not in your system's PATH.
#     # For example: psexec_custom_path="C:\\SysinternalsSuite\\PsExec.exe"
#     reg_export(
#         src=registry_paths_to_export,
#         dst_directory=output_directory,
#         dry_run=False,  # Set to True for a dry run, False for actual export
#         use_psexec=True,
#         psexec_custom_path=None,  # Set to "path/to/PsExec.exe" if not in PATH
#     )

#     # --- Example 3: Demonstrate what happens if PsExec is requested but not found ---
#     logger.info("\n--- Demonstrating PsExec not found scenario ---")
#     # This will log a critical error if PsExec.exe is not found
#     reg_export(
#         src=["HKEY_CURRENT_USER\\Control Panel\\Desktop"],
#         dst_directory="C:\\RegExports_Test",
#         dry_run=False,
#         use_psexec=True,
#         psexec_custom_path="C:\\NonExistentPath\\PsExec.exe",  # This path should not exist
#     )
