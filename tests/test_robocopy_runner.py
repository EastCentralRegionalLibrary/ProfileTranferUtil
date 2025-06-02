import os
import sys
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


@patch("subprocess.run")
def test_run_robocopy_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
    code = run_robocopy(SOURCE, DEST, dry_run=False)
    assert code == 0
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_run_robocopy_dry_run(mock_run):
    code = run_robocopy(SOURCE, DEST, dry_run=True)
    assert code == 0
    mock_run.assert_not_called()


@patch("subprocess.run")
def test_robocopy_folder(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="Partial Success", stderr="")
    code = robocopy_folder(SOURCE, DEST, EXCLUDE_FILES, EXCLUDE_DIRS)
    assert code == 1
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_copy_profile_root(mock_run):
    copy_profile_root(SOURCE, DEST, EXCLUDE_FILES)
    args = mock_run.call_args[0][0]
    assert "/XD" in args
    assert "/XF" in args
    assert any("AppData" in arg for arg in args)


@patch("os.makedirs")
@patch("subprocess.run")
def test_copy_appdata_subdirs(mock_run, mock_makedirs):
    copy_appdata_subdirs(SOURCE, DEST, SUBDIRS, EXCLUDE_DIRS)
    assert mock_run.call_count == len(SUBDIRS)
    for subdir in SUBDIRS:
        expected_dst = f"{DEST}\\{subdir}"
        mock_makedirs.assert_any_call(expected_dst, exist_ok=True)
