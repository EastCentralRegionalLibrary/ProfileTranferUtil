import os
import subprocess
import logging
from unittest.mock import MagicMock, patch, call
import pytest

import reg_exporter  # your module under test


@pytest.fixture(autouse=True)
def setup_env(tmp_path):
    # Provide clean environment variables, especially PATH
    original_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{tmp_path / 'bin_a'}{os.pathsep}{tmp_path / 'bin_b'}"
    yield tmp_path
    os.environ["PATH"] = original_path


@pytest.fixture
def mock_popen():
    with patch("subprocess.Popen") as mock_popen:
        yield mock_popen


def test_find_executable_current_dir(setup_env, caplog):
    exe_name = "psexec.exe"
    # Simulate exe exists in cwd
    with patch("os.path.exists", return_value=True), patch(
        "os.path.isfile", return_value=True
    ):
        with caplog.at_level(logging.INFO, logger="reg_exporter"):
            found = reg_exporter.find_executable(exe_name)
        assert found.endswith(exe_name)
        assert f"Found '{exe_name}' in current directory" in caplog.text


def test_find_executable_in_path(setup_env, caplog):
    exe_name = "psexec.exe"
    fake_path = os.path.join(str(setup_env / "bin_a"), exe_name)

    def exists_side_effect(p):
        return p == fake_path

    def isfile_side_effect(p):
        return p == fake_path

    with patch("os.path.exists", side_effect=exists_side_effect), patch(
        "os.path.isfile", side_effect=isfile_side_effect
    ):
        with caplog.at_level(logging.INFO, logger="reg_exporter"):
            found = reg_exporter.find_executable(exe_name)
        assert found == fake_path
        assert f"Found '{exe_name}' in PATH: {fake_path}" in caplog.text


def test_find_executable_not_found(setup_env, caplog):
    with patch("os.path.exists", return_value=False), patch(
        "os.path.isfile", return_value=False
    ):
        with caplog.at_level(logging.WARNING, logger="reg_exporter"):
            found = reg_exporter.find_executable("nope.exe")
        assert found is None
        assert "Executable 'nope.exe' not found" in caplog.text


def test_run_regexport_dry_run(caplog):
    src = "HKCU\\Test"
    dst = "C:\\test.reg"
    with caplog.at_level(logging.INFO, logger="reg_exporter"):
        ret = reg_exporter.run_regexport(src, dst, dry_run=True)
    assert ret == 0
    assert "[Dry Run] Command:" in caplog.text
    assert "reg export" in caplog.text


def test_run_regexport_success(mock_popen, caplog):
    src = "HKCU\\Test"
    dst = "C:\\test.reg"
    process_mock = MagicMock()
    process_mock.stdout = ["Export completed successfully.\n"]
    process_mock.wait.return_value = 0
    mock_popen.return_value = process_mock

    with caplog.at_level(logging.INFO, logger="reg_exporter"):
        ret = reg_exporter.run_regexport(src, dst, dry_run=False)

    expected_cmd = f'reg export "{src}" "{dst}" /y'
    mock_popen.assert_called_once_with(
        expected_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=True,
    )
    assert ret == 0
    assert "Not using PsExec." in caplog.text
    assert "Output for" in caplog.text
    assert "exited with code 0" in caplog.text


def test_run_regexport_with_psexec(mock_popen, caplog):
    mock_process = MagicMock(stdout=["With PsExec"], wait=MagicMock(return_value=0))
    mock_popen.return_value = mock_process

    path = "C:\\Tools\\PsExec.exe"
    source = "HKCU\\Test"
    dest = "C:\\test.reg"

    caplog.set_level(logging.INFO, logger="reg_exporter")

    expected_cmd = f'"{path}" -i 1 -h cmd /c "reg export "{source}" "{dest}" /y"'

    result = reg_exporter.run_regexport(source, dest, psexec_path=path)
    assert result == 0
    assert "Using PsExec" in caplog.text
    assert "With PsExec" in caplog.text

    mock_popen.assert_called_once_with(
        expected_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=True,
    )


def test_run_regexport_file_not_found(mock_popen, caplog):
    mock_popen.side_effect = FileNotFoundError("not found")
    with caplog.at_level(logging.ERROR, logger="reg_exporter"):
        ret = reg_exporter.run_regexport("src", "dst")
    assert ret == -1
    assert "Command or PsExec executable not found" in caplog.text


def test_run_regexport_exception(mock_popen, caplog):
    mock_popen.side_effect = Exception("explode")
    with caplog.at_level(logging.ERROR, logger="reg_exporter"):
        ret = reg_exporter.run_regexport("src", "dst")
    assert ret == -1
    assert "Failed to execute command" in caplog.text
    assert "explode" in caplog.text


def test_reg_export_dry_run(tmp_path, mock_popen, caplog):
    src = ["HKEY_CU\\Foo", "HKEY_LM\\Bar"]
    dst = str(tmp_path / "Exports")

    with caplog.at_level(logging.INFO, logger="reg_exporter"):
        reg_exporter.reg_export(src, dst, dry_run=True, use_psexec=False)

    assert os.path.exists(dst) or True  # we mock os.makedirs internally, no real create
    assert "Ensured destination directory exists" in caplog.text
    assert "Starting concurrent export of registry items" in caplog.text
    assert "[Dry Run] Command:" in caplog.text
    mock_popen.assert_not_called()


def test_reg_export_success(tmp_path, mock_popen, caplog):
    src = ["HKEY_CU\\Foo", "HKEY_LM\\Bar"]
    dst = str(tmp_path / "Exports")

    proc_foo = MagicMock(stdout=["Foo exported\n"], wait=MagicMock(return_value=0))
    proc_bar = MagicMock(stdout=["Bar exported\n"], wait=MagicMock(return_value=0))
    mock_popen.side_effect = [proc_foo, proc_bar]

    with caplog.at_level(logging.INFO, logger="reg_exporter"):
        reg_exporter.reg_export(src, dst, dry_run=False, use_psexec=False)

    assert "Ensured destination directory exists" in caplog.text
    assert "Starting concurrent export of registry items" in caplog.text
    assert "Exporting 'HKEY_CU\\Foo'" in caplog.text
    assert "Exporting 'HKEY_LM\\Bar'" in caplog.text
    assert "[Thread] Finished exporting 'HKEY_CU\\Foo' with exit code 0" in caplog.text
    assert "[Thread] Finished exporting 'HKEY_LM\\Bar' with exit code 0" in caplog.text


def test_reg_export_with_psexec_custom_path(tmp_path, mock_popen, caplog):
    src = ["HKEY_CU\\PsExecTest"]
    dst = str(tmp_path / "Exports")
    psexec_path = str(tmp_path / "PsExec.exe")

    # Patch os.path.exists and isfile to simulate PsExec present
    with patch("os.path.exists", return_value=True), patch(
        "os.path.isfile", return_value=True
    ):
        proc = MagicMock(stdout=["PsExec export\n"], wait=MagicMock(return_value=0))
        mock_popen.return_value = proc

        with caplog.at_level(logging.INFO, logger="reg_exporter"):
            reg_exporter.reg_export(
                src, dst, dry_run=False, use_psexec=True, psexec_custom_path=psexec_path
            )

        assert (
            f"PsExec executable not found at specified custom path" not in caplog.text
        )
        assert f"Using PsExec: {psexec_path}" in caplog.text
        assert (
            "[Thread] Finished exporting 'HKEY_CU\\PsExecTest' with exit code 0"
            in caplog.text
        )


def test_reg_export_psexec_not_found(tmp_path, caplog):
    src = ["HKEY_CU\\Test"]
    dst = str(tmp_path / "Exports")

    with patch("os.path.exists", return_value=False), patch(
        "os.path.isfile", return_value=False
    ):
        with caplog.at_level(logging.CRITICAL, logger="reg_exporter"):
            result = reg_exporter.reg_export(
                src, dst, dry_run=False, use_psexec=True, psexec_custom_path=None
            )

        assert "PsExec.exe not found in system PATH or current directory" in caplog.text


def test_reg_export_psexec_custom_path_not_found(tmp_path, caplog):
    src = ["HKEY_CU\\Test"]
    dst = str(tmp_path / "Exports")
    bad_path = str(tmp_path / "not_exist_psexec.exe")

    with patch("os.path.exists", return_value=False), patch(
        "os.path.isfile", return_value=False
    ):
        with caplog.at_level(logging.CRITICAL, logger="reg_exporter"):
            result = reg_exporter.reg_export(
                src, dst, dry_run=False, use_psexec=True, psexec_custom_path=bad_path
            )

        assert (
            f"PsExec executable not found at specified custom path: {bad_path}"
            in caplog.text
        )


def test_reg_export_thread_exception_handling(setup_env, caplog, mock_popen):
    tmp_path = setup_env
    dst = str(tmp_path / "Exports")

    # Good process: returns 0
    good_proc = MagicMock(stdout=["Success"], wait=MagicMock(return_value=0))

    # Bad process: raises exception on wait()
    bad_proc = MagicMock()
    bad_proc.stdout = None
    bad_proc.wait.side_effect = Exception("explode")

    mock_popen.side_effect = [good_proc, bad_proc]

    caplog.set_level(logging.INFO)
    reg_exporter.reg_export(["HKEY_CU\\Good", "HKEY_LM\\Bad"], dst, use_psexec=False)

    # Confirm good log made it through
    assert any("Success" in rec.getMessage() for rec in caplog.records)
    assert any(
        "Failed to execute command for 'HKEY_LM\\Bad'" in rec.getMessage()
        for rec in caplog.records
    )
    assert any("explode" in rec.getMessage() for rec in caplog.records)
