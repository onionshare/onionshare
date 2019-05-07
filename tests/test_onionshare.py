"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os

import pytest

from onionshare import OnionShare
from onionshare.common import Common


class MyOnion:
    def __init__(self, stealth=False):
        self.auth_string = 'TestHidServAuth'
        self.private_key = ''
        self.stealth = stealth
        self.scheduled_key = None

    @staticmethod
    def start_onion_service(self, await_publication=True, save_scheduled_key=False):
        return 'test_service_id.onion'


@pytest.fixture
def onionshare_obj():
    common = Common()
    return OnionShare(common, MyOnion())


class TestOnionShare:
    def test_init(self, onionshare_obj):
        assert onionshare_obj.hidserv_dir is None
        assert onionshare_obj.onion_host is None
        assert onionshare_obj.stealth is None
        assert onionshare_obj.cleanup_filenames == []
        assert onionshare_obj.local_only is False

    def test_set_stealth_true(self, onionshare_obj):
        onionshare_obj.set_stealth(True)
        assert onionshare_obj.stealth is True
        assert onionshare_obj.onion.stealth is True

    def test_set_stealth_false(self, onionshare_obj):
        onionshare_obj.set_stealth(False)
        assert onionshare_obj.stealth is False
        assert onionshare_obj.onion.stealth is False

    def test_start_onion_service(self, onionshare_obj):
        onionshare_obj.set_stealth(False)
        onionshare_obj.start_onion_service()
        assert 17600 <= onionshare_obj.port <= 17650
        assert onionshare_obj.onion_host == 'test_service_id.onion'

    def test_start_onion_service_stealth(self, onionshare_obj):
        onionshare_obj.set_stealth(True)
        onionshare_obj.start_onion_service()
        assert onionshare_obj.auth_string == 'TestHidServAuth'

    def test_start_onion_service_local_only(self, onionshare_obj):
        onionshare_obj.local_only = True
        onionshare_obj.start_onion_service()
        assert onionshare_obj.onion_host == '127.0.0.1:{}'.format(
            onionshare_obj.port)

    def test_cleanup(self, onionshare_obj, temp_dir_1024, temp_file_1024):
        onionshare_obj.cleanup_filenames = [temp_dir_1024, temp_file_1024]
        onionshare_obj.cleanup()

        assert os.path.exists(temp_dir_1024) is False
        assert os.path.exists(temp_dir_1024) is False
        assert onionshare_obj.cleanup_filenames == []
