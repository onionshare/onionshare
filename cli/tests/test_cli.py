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

    @staticmethod
    def start_onion_service(
        self, mode, mode_settings_obj, await_publication=True, save_scheduled_key=False
    ):
        return "test_service_id.onion"


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
