import os
import tempfile
from datetime import datetime
from unittest import mock

import pytest

from onionshare_cli.web.receive_mode import ReceiveModeRequest


class FakeCommon:
    @staticmethod
    def log(*args):
        pass


class FakeSettings:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def get(self, section, key):
        assert section == "receive" and key == "data_dir"
        return self.data_dir


class FakeWeb:
    def __init__(self, data_dir):
        self.common = FakeCommon()
        self.settings = FakeSettings(data_dir)


def make_request(data_dir):
    req = ReceiveModeRequest.__new__(ReceiveModeRequest)
    req.web = FakeWeb(data_dir)
    req.receive_mode_dir = None
    req.upload_error = False
    req.path = "/upload"
    return req


def test_create_receive_directory():
    """
    A receive mode directory is created when there's actual content to save.
    """
    with tempfile.TemporaryDirectory() as data_dir:
        req = make_request(data_dir)
        req._create_receive_directory()

        assert not req.upload_error
        assert os.path.isdir(req.receive_mode_dir)
        assert os.listdir(req.receive_mode_dir) == []
        assert req.receive_mode_dir.startswith(data_dir)


def test_create_receive_directory_collision():
    """
    If a directory already exists at this timestamp (perhaps someone else is
    receiving files at the same second in another tab), the next numbered
    suffix is used instead of failing.
    """
    with tempfile.TemporaryDirectory() as data_dir:
        fixed = datetime(2026, 1, 1, 12, 30, 45, 123456)
        target = os.path.join(
            data_dir, fixed.strftime("%Y-%m-%d"), fixed.strftime("%H%M%S%f")
        )
        os.makedirs(target, 0o700)

        req = make_request(data_dir)
        with mock.patch("onionshare_cli.web.receive_mode.datetime") as fake_datetime:
            fake_datetime.now.return_value = fixed
            req._create_receive_directory()

        assert not req.upload_error
        assert req.receive_mode_dir == f"{target}-1"
        assert os.path.isdir(f"{target}-1")


def test_create_receive_directory_error_does_not_save(tmp_path):
    """
    If the receive mode directory can't be created, the upload fails rather
    than continuing into a folder that was never created.
    """
    data_dir = str(tmp_path)
    date_dir = os.path.join(data_dir, datetime.now().strftime("%Y-%m-%d"))
    with open(date_dir, "w") as f:
        f.write("block")

    req = make_request(data_dir)
    req._create_receive_directory()

    assert req.upload_error
    assert not os.path.exists(req.receive_mode_dir)
    # No empty folders are left behind, other than the deliberate blocker
    assert os.listdir(data_dir) == [os.path.basename(date_dir)]


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="cannot test permission errors as root",
)
def test_create_receive_directory_permission_denied(tmp_path):
    """
    Permission errors creating the receive mode directory (previously
    unreachable, as the OSError handler caught PermissionError first) now
    report the upload's error and don't attempt to save files.
    """
    data_dir = str(tmp_path)
    os.chmod(data_dir, 0o500)
    try:
        req = make_request(data_dir)
        req._create_receive_directory()

        assert req.upload_error
        assert not os.path.exists(req.receive_mode_dir)
    finally:
        os.chmod(data_dir, 0o700)
