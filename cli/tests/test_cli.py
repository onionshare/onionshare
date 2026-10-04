import os

import pytest

from onionshare_cli import OnionShare
from onionshare_cli.common import Common
from onionshare_cli.mode_settings import ModeSettings


class MyOnion:
    def __init__(self):
        self.auth_string = "TestHidServAuth"
        self.private_key = ""
        self.scheduled_key = None
        self.tor_proc = None

    @staticmethod
    def start_onion_service(
        self,
        mode,
        mode_settings_obj,
        port=None,
        await_publication=True,
        unix_socket=None,
    ):
        return "test_service_id.onion"

    def stop_onion_service(self, mode_settings_obj):
        return None


@pytest.fixture
def onionshare_obj():
    common = Common()
    return OnionShare(common, MyOnion())


@pytest.fixture
def mode_settings_obj():
    common = Common()
    return ModeSettings(common)


class TestOnionShare:
    def test_init(self, onionshare_obj):
        assert onionshare_obj.hidserv_dir is None
        assert onionshare_obj.onion_host is None
        assert onionshare_obj.local_only is False

    def test_start_onion_service(self, onionshare_obj, mode_settings_obj):
        onionshare_obj.start_onion_service("share", mode_settings_obj)
        assert 17600 <= onionshare_obj.port <= 17650
        assert onionshare_obj.onion_host == "test_service_id.onion"

    def test_start_onion_service_local_only(self, onionshare_obj, mode_settings_obj):
        onionshare_obj.local_only = True
        onionshare_obj.start_onion_service("share", mode_settings_obj)
        assert onionshare_obj.onion_host == "127.0.0.1:{}".format(onionshare_obj.port)

    def test_choose_unix_socket_requires_bundled_tor(self, onionshare_obj):
        assert onionshare_obj.choose_unix_socket("share") is None

    def test_choose_unix_socket_with_bundled_tor(self, onionshare_obj):
        onionshare_obj.onion.tor_proc = object()
        socket_path = onionshare_obj.choose_unix_socket("share")
        assert socket_path is not None
        assert oct(os.stat(os.path.dirname(socket_path)).st_mode & 0o777) == "0o700"
        assert onionshare_obj.choose_unix_socket("share") == socket_path

    def test_choose_unix_socket_skips_chat(self, onionshare_obj):
        onionshare_obj.onion.tor_proc = object()
        assert onionshare_obj.choose_unix_socket("chat") is None

    def test_choose_unix_socket_skips_windows(self, onionshare_obj):
        onionshare_obj.onion.tor_proc = object()
        onionshare_obj.common.platform = "Windows"
        assert onionshare_obj.choose_unix_socket("share") is None

    def test_choose_unix_socket_skips_local_only(self, onionshare_obj):
        onionshare_obj.onion.tor_proc = object()
        onionshare_obj.local_only = True
        assert onionshare_obj.choose_unix_socket("share") is None

    def test_choose_unix_socket_picks_a_fresh_path_after_stop(
        self, onionshare_obj, mode_settings_obj
    ):
        onionshare_obj.onion.tor_proc = object()
        first = onionshare_obj.choose_unix_socket("share")
        assert first is not None
        assert os.path.isdir(os.path.dirname(first))

        onionshare_obj.stop_onion_service(mode_settings_obj)
        assert onionshare_obj.unix_socket is None
        assert not os.path.exists(os.path.dirname(first))

        second = onionshare_obj.choose_unix_socket("share")
        assert second is not None
        assert second != first
