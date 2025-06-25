from typing import List
import pytest
import os
import logging
from unittest.mock import patch, call
from load_config import load_config
import main


@pytest.fixture(scope="module")
def app_config():
    config = load_config()
    return {
        "config": config,
        "SYS_DISK": config["profile"]["SYS_DISK"],
        "PROGRAM_FILES_DIR": config["profile"]["PROGRAM_FILES_DIR"],
        "USER_PROFILE_SUBPATH": config["profile"]["USER_PROFILE_SUBPATH"],
        "APPDATA_NAME": config["profile"]["APPDATA_NAME"],
        "ROBOCOPY_OPTIONS": config["robocopy"]["ROBOCOPY_OPTIONS"],
        "ROBOCOPY_EXCLUDE_FILES": config["robocopy"]["ROBOCOPY_EXCLUDE_FILES"],
        "ROBOCOPY_EXCLUDE_DIRS": config["robocopy"]["ROBOCOPY_EXCLUDE_DIRS"],
        "APPDATA_LOCAL_INCLUDE_DIRS": config["robocopy"]["APPDATA_LOCAL_INCLUDE_DIRS"],
        "APPDATA_ROAMING_INCLUDE_DIRS": config["robocopy"][
            "APPDATA_ROAMING_INCLUDE_DIRS"
        ],
        "PROGRAM_FILES_X86_INCLUDE_DIRS": config["programs"][
            "PROGRAM_FILES_X86_INCLUDE_DIRS"
        ],
        "REGISTRY_INCLUDES": config["registry"]["REGISTRY_INCLUDES"],
    }


@patch("main.load_config", return_value=load_config())
@patch("main.copy_profile_root")
@patch("main.copy_appdata_subdirs")
@patch("main.copy_program_files")
@patch("main.reg_export")
@patch(
    "main.prompt_for_input",
    side_effect=[
        "RemotePC",
        "jdoe",
        "C:\\Backup",
        "y",
        "y",
        "C:",
        "y",
        "C:\\Backup",
        "y",
    ],
)
@patch("main.check_unc_access", return_value=True)
@patch("main.prompt_user_to_authenticate", return_value=True)
@patch("main.remove_mark_of_the_web_from_shortcuts")
@patch("main.sys.exit")
def test_main_dry_run(
    mock_sys_exit,
    mock_remove_motw,
    mock_prompt_user_to_authenticate,
    mock_check_unc_access,
    mock_prompt_for_input,
    mock_reg_export,
    mock_copy_program_files,
    mock_copy_appdata_subdirs,
    mock_copy_profile_root,
    mock_load_config,
    caplog,
    app_config,
):
    caplog.set_level(logging.INFO)
    unc_source = main.build_unc_source(
        "RemotePC", app_config["USER_PROFILE_SUBPATH"], "jdoe"
    )

    with patch("main.sys.argv", ["main.py", "--dryrun"]):
        main.main()

    assert any(
        "Skipping destination directory creation" in r.message for r in caplog.records
    )
    assert any("Profile transfer complete." in r.message for r in caplog.records)

    mock_copy_profile_root.assert_called_once_with(
        app_config["ROBOCOPY_OPTIONS"],
        unc_source,
        "C:\\Backup",
        exclude_dirs=app_config["APPDATA_NAME"],
        exclude_files=app_config["ROBOCOPY_EXCLUDE_FILES"],
        dry_run=True,
    )
    mock_copy_appdata_subdirs.assert_has_calls(
        [
            call(
                app_config["ROBOCOPY_OPTIONS"],
                unc_source,
                "C:\\Backup",
                app_config["APPDATA_LOCAL_INCLUDE_DIRS"],
                exclude_dirs=app_config["ROBOCOPY_EXCLUDE_DIRS"],
                dry_run=True,
            ),
            call(
                app_config["ROBOCOPY_OPTIONS"],
                unc_source,
                "C:\\Backup",
                app_config["APPDATA_ROAMING_INCLUDE_DIRS"],
                dry_run=True,
            ),
        ]
    )
    mock_copy_program_files.assert_called_once()
    mock_reg_export.assert_called_once()
    mock_remove_motw.assert_called_once()
    mock_sys_exit.assert_called_once_with(0)


@patch("main.load_config", return_value=load_config())
@patch("main.copy_profile_root")
@patch("main.copy_appdata_subdirs")
@patch("main.copy_program_files")
@patch("main.reg_export")
@patch(
    "main.prompt_for_input",
    side_effect=[
        "RemotePC",
        "jdoe",
        "C:\\ActualBackup",
        "y",
        "y",
        "C:\\",
        "y",
        "C:\\ActualBackup",
        "y",
    ],
)
@patch("main.check_unc_access", return_value=True)
@patch("main.prompt_user_to_authenticate", return_value=True)
@patch("main.ensure_directory")
@patch("main.remove_mark_of_the_web_from_shortcuts")
@patch("main.sys.exit")
def test_main_full_run_default_psexec(
    mock_sys_exit,
    mock_remove_motw,
    mock_ensure_directory,
    mock_prompt_user_to_authenticate,
    mock_check_unc_access,
    mock_prompt_for_input,
    mock_reg_export,
    mock_copy_program_files,
    mock_copy_appdata_subdirs,
    mock_copy_profile_root,
    mock_load_config,
    caplog,
):
    caplog.set_level(logging.INFO)

    with patch("main.sys.argv", ["main.py"]):
        main.main()

    assert any("Profile transfer complete." in r.message for r in caplog.records)
    mock_sys_exit.assert_called_once_with(0)


@patch("main.load_config", return_value=load_config())
@patch("main.copy_profile_root")
@patch("main.copy_appdata_subdirs")
@patch("main.copy_program_files")
@patch("main.reg_export")
@patch(
    "main.prompt_for_input",
    side_effect=[
        "RemotePC",
        "jdoe",
        "C:\\AltBackup",
        "y",
        "y",
        "C:",
        "y",
        "C:\\AltBackup",
        "y",
    ],
)
@patch("main.check_unc_access", return_value=True)
@patch("main.prompt_user_to_authenticate", return_value=True)
@patch("main.ensure_directory")
@patch("main.remove_mark_of_the_web_from_shortcuts")
@patch("main.sys.exit")
def test_main_full_run_no_psexec_flag(
    mock_sys_exit,
    mock_remove_motw,
    mock_ensure_directory,
    mock_prompt_user_to_authenticate,
    mock_check_unc_access,
    mock_prompt_for_input,
    mock_reg_export,
    mock_copy_program_files,
    mock_copy_appdata_subdirs,
    mock_copy_profile_root,
    mock_load_config,
    caplog,
):
    caplog.set_level(logging.INFO)

    with patch("main.sys.argv", ["main.py", "--no-psexec"]):
        main.main()

    assert any("Profile transfer complete." in r.message for r in caplog.records)
    mock_sys_exit.assert_called_once_with(0)
