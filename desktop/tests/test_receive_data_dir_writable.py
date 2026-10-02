# -*- coding: utf-8 -*-
"""Unit tests for ReceiveMode save-folder writability checks (#2062)."""

import os
import stat
import tempfile

# Desktop tests run with the onionshare package on PYTHONPATH
from onionshare.tab.mode.receive_mode import ReceiveMode


def test_is_data_dir_writable_ok(tmp_path):
    assert ReceiveMode.is_data_dir_writable(str(tmp_path)) is True


def test_is_data_dir_writable_missing():
    assert (
        ReceiveMode.is_data_dir_writable("/path/that/does/not/exist-onionshare")
        is False
    )


def test_is_data_dir_writable_file_not_dir(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    assert ReceiveMode.is_data_dir_writable(str(f)) is False


def test_is_data_dir_writable_readonly_dir():
    # Best-effort: skip if this OS cannot make a non-writable directory (e.g. Windows)
    with tempfile.TemporaryDirectory() as d:
        try:
            os.chmod(d, stat.S_IRUSR | stat.S_IXUSR)
            if ReceiveMode.is_data_dir_writable(d):
                # Platform did not honor read-only; don't fail the suite
                return
            assert ReceiveMode.is_data_dir_writable(d) is False
        finally:
            try:
                os.chmod(d, stat.S_IRWXU)
            except OSError:
                pass


def test_create_missing_receive_dir(tmp_path):
    path = tmp_path / "OnionShare"
    assert ReceiveMode.is_data_dir_writable(str(path), create=True)
    assert path.is_dir()
    assert list(path.iterdir()) == []
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o700


def test_missing_dir_probe_does_not_create(tmp_path):
    path = tmp_path / "missing"
    assert not ReceiveMode.is_data_dir_writable(str(path))
    assert not path.exists()


def test_create_receive_dir_rejects_file(tmp_path):
    path = tmp_path / "file"
    path.write_text("preserve me")
    assert not ReceiveMode.is_data_dir_writable(str(path), create=True)
    assert path.read_text() == "preserve me"


def test_create_receive_dir_permission_error(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("Directory creation denied")

    monkeypatch.setattr(os, "makedirs", denied)
    assert not ReceiveMode.is_data_dir_writable(str(tmp_path / "missing"), create=True)


def test_receive_dir_write_probe_failure(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("Write denied by sandbox")

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", denied)
    assert not ReceiveMode.is_data_dir_writable(str(tmp_path), create=True)
    assert list(tmp_path.iterdir()) == []
