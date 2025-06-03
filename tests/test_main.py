import pytest
from unittest.mock import patch, MagicMock
from load_config import load_config
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
    
    config = load_config()

    USER_PROFILE_SUBPATH: str = config["profile"]["USER_PROFILE_SUBPATH"]
    ROBOCOPY_OPTIONS: List[str] = config["robocopy"]["ROBOCOPY_OPTIONS"]
    ROBOCOPY_EXCLUDE_FILES: List[str] = config["robocopy"]["ROBOCOPY_EXCLUDE_FILES"]
    ROBOCOPY_EXCLUDE_DIRS: List[str] = config["robocopy"]["ROBOCOPY_EXCLUDE_DIRS"]
    APPDATA_LOCAL_INCLUDE_DIRS: List[str] = config["robocopy"][
        "APPDATA_LOCAL_INCLUDE_DIRS"
    ]
    APPDATA_ROAMING_INCLUDE_DIRS: List[str] = config["robocopy"][
        "APPDATA_ROAMING_INCLUDE_DIRS"
    ]

    with patch("main.sys.argv", ["main.py", "--dryrun"]), patch(
        "main.sys.exit"
    ) as mock_exit:
        main.main()

    unc_path = r"\\RemotePC\C$\Users\jdoe"
    dest_path = r"C:\Backup"

    mock_copy_root.assert_called_once_with(
        ROBOCOPY_OPTIONS,
        unc_path,
        dest_path,
        exclude_files=ROBOCOPY_EXCLUDE_FILES,
        dry_run=True,
    )
    # The first call is for APPDATA_LOCAL_INCLUDE_DIRS
    mock_copy_appdata.assert_any_call(
        ROBOCOPY_OPTIONS,
        unc_path,
        dest_path,
        APPDATA_LOCAL_INCLUDE_DIRS,
        exclude_dirs=ROBOCOPY_EXCLUDE_DIRS,
        dry_run=True,
    )
    # The second call is for APPDATA_ROAMING_INCLUDE_DIRS
    mock_copy_appdata.assert_any_call(
        ROBOCOPY_OPTIONS,
        unc_path,
        dest_path,
        APPDATA_ROAMING_INCLUDE_DIRS,
        dry_run=True,
    )
    mock_remove_motw.assert_called_once()
