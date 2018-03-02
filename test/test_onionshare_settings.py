"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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

import json
import os
import tempfile

import pytest

from onionshare import common, settings, strings


@pytest.fixture
def custom_version(monkeypatch):
    monkeypatch.setattr(common, 'get_version', lambda: 'DUMMY_VERSION_1.2.3')


@pytest.fixture
def os_path_expanduser(monkeypatch):
    monkeypatch.setattr('os.path.expanduser', lambda path: path)


@pytest.fixture
def settings_obj(custom_version, sys_onionshare_dev_mode, platform_linux):
    return settings.Settings()


class TestSettings:
    def test_init(self, settings_obj):
        assert settings_obj._settings == settings_obj.default_settings == {
            'version': 'DUMMY_VERSION_1.2.3',
            'connection_type': 'bundled',
            'control_port_address': '127.0.0.1',
            'control_port_port': 9051,
            'socks_address': '127.0.0.1',
            'socks_port': 9050,
            'socket_file_path': '/var/run/tor/control',
            'auth_type': 'no_auth',
            'auth_password': '',
            'minimize_to_tray_on_close': False,
            'close_after_first_download': True,
            'systray_notifications': True,
            'shutdown_timeout': False,
            'use_stealth': False,
            'use_autoupdate': True,
            'autoupdate_timestamp': None,
            'no_bridges': True,
            'tor_bridges_use_obfs4': False,
            'tor_bridges_use_meek_lite_amazon': False,
            'tor_bridges_use_meek_lite_azure': False,
            'tor_bridges_use_custom_bridges': '',
            'save_private_key': False,
            'private_key': '',
            'slug': '',
            'hidservauth_string': ''
        }

    def test_fill_in_defaults(self, settings_obj):
        del settings_obj._settings['version']
        settings_obj.fill_in_defaults()
        assert settings_obj._settings['version'] == 'DUMMY_VERSION_1.2.3'

    def test_load(self, settings_obj):
        custom_settings = {
            'version': 'CUSTOM_VERSION',
            'socks_port': 9999,
            'use_stealth': True
        }
        tmp_file, tmp_file_path = tempfile.mkstemp()
        with open(tmp_file, 'w') as f:
            json.dump(custom_settings, f)
        settings_obj.filename = tmp_file_path
        settings_obj.load()

        assert settings_obj._settings['version'] == 'CUSTOM_VERSION'
        assert settings_obj._settings['socks_port'] == 9999
        assert settings_obj._settings['use_stealth'] is True

        os.remove(tmp_file_path)
        assert os.path.exists(tmp_file_path) is False

    def test_save(self, monkeypatch, settings_obj):
        monkeypatch.setattr(strings, '_', lambda _: '')

        settings_filename = 'default_settings.json'
        tmp_dir = tempfile.gettempdir()
        settings_path = os.path.join(tmp_dir, settings_filename)
        settings_obj.filename = settings_path
        settings_obj.save()
        with open(settings_path, 'r') as f:
            settings = json.load(f)

        assert settings_obj._settings == settings

        os.remove(settings_path)
        assert os.path.exists(settings_path) is False

    def test_get(self, settings_obj):
        assert settings_obj.get('version') == 'DUMMY_VERSION_1.2.3'
        assert settings_obj.get('connection_type') == 'bundled'
        assert settings_obj.get('control_port_address') == '127.0.0.1'
        assert settings_obj.get('control_port_port') == 9051
        assert settings_obj.get('socks_address') == '127.0.0.1'
        assert settings_obj.get('socks_port') == 9050
        assert settings_obj.get('socket_file_path') == '/var/run/tor/control'
        assert settings_obj.get('auth_type') == 'no_auth'
        assert settings_obj.get('auth_password') == ''
        assert settings_obj.get('minimize_to_tray_on_close') is False
        assert settings_obj.get('close_after_first_download') is True
        assert settings_obj.get('systray_notifications') is True
        assert settings_obj.get('use_stealth') is False
        assert settings_obj.get('use_autoupdate') is True
        assert settings_obj.get('autoupdate_timestamp') is None
        assert settings_obj.get('autoupdate_timestamp') is None
        assert settings_obj.get('no_bridges') is True
        assert settings_obj.get('tor_bridges_use_obfs4') is False
        assert settings_obj.get('tor_bridges_use_meek_lite_amazon') is False
        assert settings_obj.get('tor_bridges_use_meek_lite_azure') is False
        assert settings_obj.get('tor_bridges_use_custom_bridges') == ''


    def test_set_version(self, settings_obj):
        settings_obj.set('version', 'CUSTOM_VERSION')
        assert settings_obj._settings['version'] == 'CUSTOM_VERSION'

    def test_set_control_port_port(self, settings_obj):
        settings_obj.set('control_port_port', 999)
        assert settings_obj._settings['control_port_port'] == 999

        settings_obj.set('control_port_port', 'NON_INTEGER')
        assert settings_obj._settings['control_port_port'] == 9051

    def test_set_socks_port(self, settings_obj):
        settings_obj.set('socks_port', 888)
        assert settings_obj._settings['socks_port'] == 888

        settings_obj.set('socks_port', 'NON_INTEGER')
        assert settings_obj._settings['socks_port'] == 9050

    def test_filename_darwin(
            self,
            custom_version,
            monkeypatch,
            os_path_expanduser,
            platform_darwin):
        obj = settings.Settings()
        assert (obj.filename ==
                '~/Library/Application Support/OnionShare/onionshare.json')

    def test_filename_linux(
            self,
            custom_version,
            monkeypatch,
            os_path_expanduser,
            platform_linux):
        obj = settings.Settings()
        assert obj.filename == '~/.config/onionshare/onionshare.json'

    def test_filename_windows(
            self,
            custom_version,
            monkeypatch,
            platform_windows):
        monkeypatch.setenv('APPDATA', 'C:')
        obj = settings.Settings()
        assert obj.filename == 'C:\\OnionShare\\onionshare.json'

    def test_set_custom_bridge(self, settings_obj):
        settings_obj.set('tor_bridges_use_custom_bridges', 'Bridge 45.3.20.65:9050 21300AD88890A49C429A6CB9959CFD44490A8F6E')
        assert settings_obj._settings['tor_bridges_use_custom_bridges'] == 'Bridge 45.3.20.65:9050 21300AD88890A49C429A6CB9959CFD44490A8F6E'
