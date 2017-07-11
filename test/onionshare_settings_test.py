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
from unittest.mock import Mock, call

import pytest

from onionshare import common, settings, strings


@pytest.fixture
def common_get_version(monkeypatch):
    monkeypatch.setattr(common, 'get_version', lambda: 'DUMMY_VERSION_1.2.3')


@pytest.fixture
def mock_common_log(monkeypatch):
    m = Mock()
    monkeypatch.setattr(common, 'log', m)
    return m


@pytest.fixture
def mock_json_loads(monkeypatch):
    m = Mock(spec=json.loads)
    monkeypatch.setattr('json.loads', m)
    return m


@pytest.fixture
def mock_os_path(monkeypatch):
    m = Mock()
    monkeypatch.setattr('os.path', m)
    return m


@pytest.fixture
def os_path_expanduser(monkeypatch):
    monkeypatch.setattr('os.path.expanduser', lambda path: path)


@pytest.fixture
def settings_obj_default(common_get_version, sys_onionshare_dev_mode, platform_linux):
    return settings.Settings()


@pytest.fixture
def settings_obj_custom(common_get_version, sys_onionshare_dev_mode, platform_linux):
    return settings.Settings(config='test_config.json')


class TestSettings:
    def test_custom_config_exists(
            self,
            common_get_version,
            mock_common_log,
            mock_os_path):

        config_filename = 'test_config.json'
        mock_os_path.isfile.return_value = True

        settings_obj = settings.Settings(config=config_filename)

        mock_common_log.assert_called_once_with('Settings', '__init__')
        mock_os_path.isfile.assert_called_once_with(config_filename)
        assert settings_obj.filename == config_filename

    def test_custom_config_doesnt_exist(
            self,
            common_get_version,
            mock_common_log,
            mock_os_path):

        config_filename = 'test_config.json'
        mock_os_path.isfile.return_value = False

        settings.Settings(config=config_filename)

        mock_os_path.isfile.assert_called_once_with(config_filename)
        mock_common_log.assert_has_calls((
            call('Settings', '__init__'),
            call('Settings', '__init__', (
                'Supplied config does not exist or is unreadable. '
                'Falling back to default location'))
        ))

    def test_default_init(self, settings_obj_default):
        assert settings_obj_default._settings == settings_obj_default.default_settings == {
            'version': 'DUMMY_VERSION_1.2.3',
            'connection_type': 'bundled',
            'control_port_address': '127.0.0.1',
            'control_port_port': 9051,
            'socks_address': '127.0.0.1',
            'socks_port': 9050,
            'socket_file_path': '/var/run/tor/control',
            'auth_type': 'no_auth',
            'auth_password': '',
            'close_after_first_download': True,
            'systray_notifications': True,
            'use_stealth': False,
            'use_autoupdate': True,
            'autoupdate_timestamp': None
        }

    def test_fill_in_defaults(self, settings_obj_default):
        del settings_obj_default._settings['version']

        settings_obj_default.fill_in_defaults()

        assert (settings_obj_default._settings['version'] ==
                'DUMMY_VERSION_1.2.3')

    def test_load(self, settings_obj_default):
        custom_version = 'CUSTOM_VERSION'
        custom_socks_port = 9999
        custom_use_stealth = True
        custom_settings = {
            'version': custom_version,
            'socks_port': custom_socks_port,
            'use_stealth': custom_use_stealth
        }
        # create temporary config file
        tmp_file, tmp_file_path = tempfile.mkstemp()
        with open(tmp_file, 'w') as f:
            json.dump(custom_settings, f)

        # load config file into Settings instance
        settings_obj_default.filename = tmp_file_path
        settings_obj_default.load()

        # test that the custom settings were applied
        assert settings_obj_default._settings['version'] == custom_version
        assert settings_obj_default._settings['socks_port'] == custom_socks_port
        assert settings_obj_default._settings['use_stealth'] == custom_use_stealth

        # delete temporary config file
        os.remove(tmp_file_path)
        assert os.path.exists(tmp_file_path) is False

    def test_load_bad_json_raises(
            self,
            common_get_version,
            mock_common_log,
            mock_json_loads,
            monkeypatch,
            settings_obj_default):

        # create a temporary config file with invalid JSON
        bad_json = '{"BAD_JSON": 1'
        tmp_file, tmp_file_path = tempfile.mkstemp()
        with open(tmp_file, 'w') as f:
            f.write(bad_json)

        # raise JSONDecodeError when trying to load JSON config file
        mock_json_loads.side_effect = json.JSONDecodeError

        # create a new Settings instance with custom config file
        settings_obj = settings.Settings(config=tmp_file_path)
        settings_obj.load()

        mock_common_log.assert_has_calls((
            call('Settings', '__init__'),
            call('Settings', '__init__'),
            call('Settings', 'load'),
            call('Settings', 'load', 'Trying to load {}'.format(
                tmp_file_path))
        ))

        # test that json.loads was called once
        mock_json_loads.assert_called_once_with(bad_json)

        # delete temporary config file
        os.remove(tmp_file_path)
        assert os.path.exists(tmp_file_path) is False

    def test_save(self, monkeypatch, settings_obj_default):
        monkeypatch.setattr(strings, '_', lambda _: '')

        # create a file to save the default settings
        settings_filename = 'default_settings.json'
        tmp_dir = tempfile.gettempdir()
        settings_path = os.path.join(tmp_dir, settings_filename)

        # save the default settings to that file
        settings_obj_default.filename = settings_path
        settings_obj_default.save()

        # load the settings from the file
        with open(settings_path, 'r') as f:
            settings = json.load(f)

        # test that the proper settings were saved to the file
        assert settings_obj_default._settings == settings

        # delete temporary config file
        os.remove(settings_path)
        assert os.path.exists(settings_path) is False

    def test_get(self, settings_obj_default):
        assert settings_obj_default.get('version') == 'DUMMY_VERSION_1.2.3'
        assert settings_obj_default.get('connection_type') == 'bundled'
        assert settings_obj_default.get('control_port_address') == '127.0.0.1'
        assert settings_obj_default.get('control_port_port') == 9051
        assert settings_obj_default.get('socks_address') == '127.0.0.1'
        assert settings_obj_default.get('socks_port') == 9050
        assert settings_obj_default.get('socket_file_path') == '/var/run/tor/control'
        assert settings_obj_default.get('auth_type') == 'no_auth'
        assert settings_obj_default.get('auth_password') == ''
        assert settings_obj_default.get('close_after_first_download') is True
        assert settings_obj_default.get('systray_notifications') is True
        assert settings_obj_default.get('use_stealth') is False
        assert settings_obj_default.get('use_autoupdate') is True
        assert settings_obj_default.get('autoupdate_timestamp') is None

    def test_set(self, settings_obj_default):
        settings_obj_default.set('version', 'CUSTOM_VERSION')
        assert settings_obj_default._settings['version'] == 'CUSTOM_VERSION'

        settings_obj_default.set('control_port_port', 999)
        assert settings_obj_default._settings['control_port_port'] == 999

        # test that values fall back to default if not found
        settings_obj_default.set('control_port_port', 'NON_INTEGER')
        assert settings_obj_default._settings['control_port_port'] == 9051

        settings_obj_default.set('socks_port', 888)
        assert settings_obj_default._settings['socks_port'] == 888

        # test that values fall back to default if not found
        settings_obj_default.set('socks_port', 'NON_INTEGER')
        assert settings_obj_default._settings['socks_port'] == 9050

    def test_filename_darwin(
            self,
            common_get_version,
            monkeypatch,
            os_path_expanduser,
            platform_darwin):
        obj = settings.Settings()
        assert (obj.filename ==
                '~/Library/Application Support/OnionShare/onionshare.json')

    def test_filename_linux(
            self,
            common_get_version,
            monkeypatch,
            os_path_expanduser,
            platform_linux):

        obj = settings.Settings()
        assert obj.filename == '~/.config/onionshare/onionshare.json'

    def test_filename_windows(
            self,
            common_get_version,
            monkeypatch,
            os_path_expanduser,
            platform_windows):

        monkeypatch.setenv('APPDATA', 'C:')
        obj = settings.Settings()
        assert obj.filename == 'C:\\OnionShare\\onionshare.json'
