# tests/test_unc_utils.py

import os
import sys
import pytest
from unittest import mock

# Add root directory to path to import unc_utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unc_utils import check_unc_access, prompt_user_to_authenticate


def test_check_unc_access_existing_path(tmp_path):
    """Test check_unc_access returns True for an existing path."""
    assert check_unc_access(str(tmp_path)) is True


def test_check_unc_access_nonexistent_path():
    """Test check_unc_access returns False for a non-existent path."""
    assert check_unc_access(r"\\This\Path\Should\Not\Exist") is False


@mock.patch("subprocess.Popen")
def test_prompt_user_to_authenticate_success(mock_popen):
    """Test prompt_user_to_authenticate returns True when window is closed in time."""
    mock_proc = mock.Mock()
    mock_proc.poll.side_effect = [None, None, 0]  # Simulate closing after 3 loops
    mock_popen.return_value = mock_proc

    result = prompt_user_to_authenticate(r"\\FakeUNC\C$", timeout=5)
    assert result is True


@mock.patch("subprocess.Popen")
def test_prompt_user_to_authenticate_timeout(mock_popen):
    """Test prompt_user_to_authenticate returns False on timeout."""
    mock_proc = mock.Mock()
    mock_proc.poll.return_value = None  # Never closes
    mock_popen.return_value = mock_proc

    result = prompt_user_to_authenticate(r"\\FakeUNC\C$", timeout=1)
    assert result is False


@mock.patch("subprocess.Popen", side_effect=Exception("Launch failed"))
def test_prompt_user_to_authenticate_exception(mock_popen):
    """Test prompt_user_to_authenticate returns False on exception."""
    result = prompt_user_to_authenticate(r"\\FakeUNC\C$", timeout=1)
    assert result is False
