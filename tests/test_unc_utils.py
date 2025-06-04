# tests/test_unc_utils.py

import os
import sys
import pytest
from unittest import mock

# Add root directory to path to import unc_utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unc_utils import check_unc_access, prompt_user_to_authenticate

unc_root = r"\\FakeUNC\C$"


def test_check_unc_access_existing_path(tmp_path):
    """Test check_unc_access returns True for an existing path."""
    assert check_unc_access(str(tmp_path)) is True


def test_check_unc_access_nonexistent_path():
    """Test check_unc_access returns False for a non-existent path."""
    assert check_unc_access(r"\\This\Path\Should\Not\Exist") is False


@mock.patch("subprocess.Popen")
@mock.patch(
    "os.path.exists", side_effect=[False, False, True]
)  # simulate eventual access
def test_prompt_user_to_authenticate_success(mock_exists, mock_pOpen):
    """Test prompt_user_to_authenticate returns True when UNC path becomes accessible."""
    result = prompt_user_to_authenticate(unc_root, timeout=5, interval=0.1)
    assert result is True
    mock_pOpen.assert_called_once_with(
        f"cmd /c explorer {unc_root}",
        shell=True,
    )


@mock.patch("subprocess.Popen")
@mock.patch("os.path.exists", return_value=False)
def test_prompt_user_to_authenticate_timeout(mock_exists, mock_pOpen):
    """Test prompt_user_to_authenticate returns False on timeout without access."""
    result = prompt_user_to_authenticate(unc_root, timeout=0.3, interval=0.1)
    assert result is False
    mock_pOpen.assert_called_once_with(
        f"cmd /c explorer {unc_root}",
        shell=True,
    )


@mock.patch("subprocess.Popen", side_effect=Exception("Launch failed"))
def test_prompt_user_to_authenticate_exception(mock_pOpen):
    """Test prompt_user_to_authenticate returns False on exception."""
    result = prompt_user_to_authenticate(unc_root)
    assert result is False
