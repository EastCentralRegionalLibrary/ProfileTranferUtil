import os
import sys
import io
import pytest
from unittest.mock import patch, call, MagicMock

# Add root project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Adjust this import to match your file name if needed
from robocopy_runner import (
    run_robocopy,
    robocopy_folder,
    copy_profile_root,
    copy_appdata_subdirs,
)

# Sample data for use across tests
SOURCE = r"C:\Users\TestUser"
DEST = r"D:\Backup\TestUser"
SUBDIRS = [
    "AppData\\Local\\Google\\Chrome\\User Data\\Default",
    "AppData\\Roaming\\Mozilla",
]
EXCLUDE_FILES = ["NTUSER.DAT"]
EXCLUDE_DIRS = ["Temp"]


@patch("subprocess.Popen")
def test_run_robocopy_success(mock_popen):
    mock_process = MagicMock()
    mock_process.stdout = io.StringIO("Success\n")
    mock_process.wait.return_value = 0
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    code = run_robocopy(SOURCE, DEST, dry_run=False)
    assert code == 0


@patch("subprocess.Popen")
def test_run_robocopy_dry_run(mock_popen):
    code = run_robocopy(SOURCE, DEST, dry_run=True)
    assert code == 0
    mock_popen.assert_not_called()


@patch("subprocess.Popen")
def test_robocopy_folder(mock_popen):
    mock_process = MagicMock()
    mock_process.stdout = io.StringIO("Partial Success\n")
    mock_process.wait.return_value = 1
    mock_process.returncode = 1
    mock_popen.return_value = mock_process

    code = robocopy_folder(SOURCE, DEST, EXCLUDE_FILES, EXCLUDE_DIRS)
    assert code == 1


@patch("subprocess.Popen")
def test_copy_profile_root(mock_popen):
    mock_process = MagicMock()
    mock_process.stdout = ["Copying root\n"]
    mock_process.wait.return_value = None
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    copy_profile_root(SOURCE, DEST, EXCLUDE_FILES)
    args = mock_popen.call_args[0][0]
    assert "/XD" in args
    assert "/XF" in args
    assert any("AppData" in arg for arg in args)


@patch("os.makedirs")
@patch("robocopy_runner.robocopy_folder")
def test_copy_appdata_subdirs(mock_robocopy_folder, mock_makedirs):
    mock_robocopy_folder.return_value = 0  # Simulate success

    copy_appdata_subdirs(SOURCE, DEST, SUBDIRS, EXCLUDE_DIRS)

    assert mock_robocopy_folder.call_count == len(SUBDIRS)

    for subdir in SUBDIRS:
        expected_dst = os.path.join(DEST, subdir)
        mock_makedirs.assert_any_call(expected_dst, exist_ok=True)
