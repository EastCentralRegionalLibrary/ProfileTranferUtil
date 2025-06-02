import pytest
from unittest.mock import patch, MagicMock
import main


@patch("main.copy_profile_root")
@patch("main.copy_appdata_subdirs")
@patch("main.prompt_for_input", side_effect=["RemotePC", "jdoe", "C:\\Backup", "y", "y"])
@patch("main.check_unc_access", return_value=True)
@patch("main.ensure_directory")
@patch("main.remove_mark_of_the_web_from_shortcuts")
def test_main_dry_run(
    mock_remove_motw,
    mock_ensure_dir,
    mock_check_access,
    mock_prompt,
    mock_copy_appdata,
    mock_copy_root,
):
    with patch("main.sys.argv", ["main.py", "--dryrun"]), patch(
        "main.sys.exit"
    ) as mock_exit:
        main.main()

    unc_path = r"\\RemotePC\C$\Users\jdoe"
    dest_path = r"C:\Backup"

    mock_copy_root.assert_called_once_with(
        unc_path,
        dest_path,
        exclude_files=main.ROBOCOPY_EXCLUDE_FILES,
        dry_run=True,
    )
    # The first call is for APPDATA_LOCAL_INCLUDE_DIRS
    mock_copy_appdata.assert_any_call(
        unc_path,
        dest_path,
        main.APPDATA_LOCAL_INCLUDE_DIRS,
        exclude_dirs=main.ROBOCOPY_EXCLUDE_DIRS,
        dry_run=True,
    )
    # The second call is for APPDATA_ROAMING_INCLUDE_DIRS
    mock_copy_appdata.assert_any_call(
        unc_path,
        dest_path,
        main.APPDATA_ROAMING_INCLUDE_DIRS,
        dry_run=True,
    )
    mock_remove_motw.assert_called_once()
