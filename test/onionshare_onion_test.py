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

import time
from unittest.mock import Mock, call

import pytest

from onionshare import onion, common, Onion, strings

TEST_TOR_PATH = 'TEST_TOR_PATH'
TEST_TOR_GEO_IP_FILE_PATH = 'TEST_TOR_GEO_IP_FILE_PATH'
TEST_TOR_GEO_IPV6_FILE_PATH = 'TEST_TOR_GEO_IPV6_FILE_PATH'


@pytest.fixture
def common_get_tor_paths(monkeypatch):
    monkeypatch.setattr(common, 'get_tor_paths', lambda: (
        TEST_TOR_PATH,
        TEST_TOR_GEO_IP_FILE_PATH,
        TEST_TOR_GEO_IPV6_FILE_PATH
    ))


@pytest.fixture
def mock_common_log(monkeypatch):
    m = Mock(spec=common.log)
    monkeypatch.setattr(common, 'log', m)
    return m


@pytest.fixture
def mock_strings_(monkeypatch):
    m = Mock()
    monkeypatch.setattr(strings, '_', m)
    return m


@pytest.fixture
def mock_time_sleep(monkeypatch):
    m = Mock(spec=time.sleep)
    monkeypatch.setattr('time.sleep', m)
    return m


class TestOnion:
    def test_init_darwin(
            self,
            common_get_tor_paths,
            mock_common_log,
            platform_darwin,
            sys_onionshare_dev_mode):

        onion_darwin = Onion()

        mock_common_log.assert_called_once_with('Onion', '__init__')
        assert onion_darwin.stealth is False
        assert onion_darwin.service_id is None
        assert onion_darwin.system == 'Darwin'
        assert onion_darwin.bundle_tor_supported is False
        assert onion_darwin.tor_path == TEST_TOR_PATH
        assert onion_darwin.tor_geo_ip_file_path == TEST_TOR_GEO_IP_FILE_PATH
        assert (onion_darwin.tor_geo_ipv6_file_path ==
                TEST_TOR_GEO_IPV6_FILE_PATH)
        assert onion_darwin.tor_proc is None
        assert onion_darwin.connected_to_tor is False

    def test_init_linux(
            self,
            common_get_tor_paths,
            mock_common_log,
            platform_linux):

        onion_linux = Onion()

        mock_common_log.assert_called_once_with('Onion', '__init__')
        assert onion_linux.stealth is False
        assert onion_linux.service_id is None
        assert onion_linux.system == 'Linux'
        assert onion_linux.bundle_tor_supported is True
        assert onion_linux.tor_path == TEST_TOR_PATH
        assert onion_linux.tor_geo_ip_file_path == TEST_TOR_GEO_IP_FILE_PATH
        assert onion_linux.tor_geo_ipv6_file_path == TEST_TOR_GEO_IPV6_FILE_PATH
        assert onion_linux.tor_proc is None
        assert onion_linux.connected_to_tor is False

    def test_init_windows(
            self,
            common_get_tor_paths,
            mock_common_log,
            platform_windows,
            sys_onionshare_dev_mode):

        onion_windows = Onion()

        mock_common_log.assert_called_once_with('Onion', '__init__')
        assert onion_windows.stealth is False
        assert onion_windows.service_id is None
        assert onion_windows.system == 'Windows'
        assert onion_windows.bundle_tor_supported is False
        assert onion_windows.tor_path == TEST_TOR_PATH
        assert onion_windows.tor_geo_ip_file_path == TEST_TOR_GEO_IP_FILE_PATH
        assert onion_windows.tor_geo_ipv6_file_path == TEST_TOR_GEO_IPV6_FILE_PATH
        assert onion_windows.tor_proc is None
        assert onion_windows.connected_to_tor is False

    def test_connect(self):
        pass

    def test_start_onion_service_no_ephemeral(
            self,
            mock_common_log,
            mock_strings_,
            platform_linux):

        onion_obj = Onion()
        onion_obj.supports_ephemeral = False

        with pytest.raises(onion.TorTooOld):
            onion_obj.start_onion_service(9999)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'start_onion_service')
        ))
        mock_strings_.assert_called_once_with('error_ephemeral_not_supported')

    def test_start_onion_service_no_stealth(
            self,
            mock_common_log,
            mock_strings_,
            platform_linux):

        onion_obj = Onion()
        onion_obj.stealth = True
        onion_obj.supports_ephemeral = True
        onion_obj.supports_stealth = False

        with pytest.raises(onion.TorTooOld):
            onion_obj.start_onion_service(9999)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'start_onion_service')
        ))
        mock_strings_.assert_called_once_with('error_stealth_not_supported')

    def test_start_onion_service_protocol_error(
            self,
            mock_common_log,
            mock_strings_,
            platform_linux):

        onion_obj = Onion()
        onion_obj.stealth = True
        onion_obj.supports_ephemeral = True
        onion_obj.supports_stealth = True
        onion_obj.c = Mock()
        (onion_obj.
         c.
         create_ephemeral_hidden_service.
         side_effect) = onion.TorErrorProtocolError
        test_port = 9999

        with pytest.raises(onion.TorErrorProtocolError):
            onion_obj.start_onion_service(test_port)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'start_onion_service')
        ))
        mock_strings_.assert_has_calls((
            call('config_onion_service'),
            call().format(test_port),
            call('using_ephemeral')
        ))

    def test_start_onion_service_stealth(
            self,
            mock_common_log,
            mock_strings_,
            platform_linux):

        onion_obj = Onion()
        onion_obj.stealth = True
        onion_obj.supports_ephemeral = True
        onion_obj.supports_stealth = True
        onion_obj.c = Mock()
        test_auth_cookie = 'TEST_AUTH_COOKIE'
        test_port = 9999
        test_service_id = 'TEST_SERVICE_ID'
        (onion_obj.
         c.
         create_ephemeral_hidden_service.
         return_value.
         content.
         return_value) = (
            ('', '', '={}'.format(test_service_id)), '',
            ('', '', '=:{}'.format(test_auth_cookie)))

        assert (onion_obj.start_onion_service(test_port) ==
                '{}.onion'.format(test_service_id))
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'start_onion_service')
        ))
        mock_strings_.assert_has_calls((
            call('config_onion_service'),
            call().format(test_port),
            call('using_ephemeral')
        ))
        (onion_obj.
         c.
         create_ephemeral_hidden_service.
         assert_called_once_with({80: test_port}, await_publication=True, basic_auth={'onionshare': None}))
        assert (onion_obj.
                c.
                create_ephemeral_hidden_service.
                return_value.
                content.
                call_count) == 2
        assert (onion_obj.auth_string ==
                'HidServAuth {}.onion {}'.format(
                    test_service_id, test_auth_cookie
                ))

    def test_start_onion_service(
            self,
            mock_common_log,
            mock_strings_,
            platform_linux):

        onion_obj = Onion()
        onion_obj.supports_ephemeral = True
        onion_obj.c = Mock()
        test_auth_cookie = 'TEST_AUTH_COOKIE'
        test_port = 9999
        test_service_id = 'TEST_SERVICE_ID'
        (onion_obj.
         c.
         create_ephemeral_hidden_service.
         return_value.
         content.
         return_value) = (
            ('', '', '={}'.format(test_service_id)), '',
            ('', '', '=:{}'.format(test_auth_cookie)))

        assert (onion_obj.start_onion_service(test_port) ==
                '{}.onion'.format(test_service_id))
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'start_onion_service')
        ))
        mock_strings_.assert_has_calls((
            call('config_onion_service'),
            call().format(test_port),
            call('using_ephemeral')
        ))
        (onion_obj.
         c.
         create_ephemeral_hidden_service.
         assert_called_once_with({80: test_port}, await_publication=True))
        (onion_obj.
         c.
         create_ephemeral_hidden_service.
         return_value.
         content.
         assert_called_once_with())

    def test_cleanup(
            self,
            mock_common_log,
            mock_time_sleep,
            platform_linux):

        onion_obj = Onion()
        test_service_id = 'TEST_SERVICE_ID'
        onion_obj.service_id = test_service_id
        onion_obj.tor_proc = Mock()
        (onion_obj.
         tor_proc.
         poll.
         return_value) = False
        onion_obj.c = Mock()
        (onion_obj.
         c.
         remove_ephemeral_hidden_service.
         side_effect) = Exception

        onion_obj.cleanup()

        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'cleanup')
        ))
        (onion_obj.
         c.
         remove_ephemeral_hidden_service.
         assert_called_once_with(test_service_id))
        mock_time_sleep.assert_called_once_with(0.2)
        assert onion_obj.service_id is None
        assert onion_obj.tor_proc is None
        assert onion_obj.connected_to_tor is False
        assert onion_obj.stealth is False

    def test_get_tor_socks_port_bundled(
            self,
            mock_common_log,
            platform_linux):

        onion_obj = Onion()
        onion_obj.settings = Mock()
        onion_obj.settings.get.return_value = 'bundled'
        test_tor_socks_port = 9999
        onion_obj.tor_socks_port = test_tor_socks_port

        assert onion_obj.get_tor_socks_port() == ('127.0.0.1', test_tor_socks_port)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'get_tor_socks_port')
        ))
        (onion_obj.
         settings.
         get.
         assert_called_once_with('connection_type'))

    def test_get_tor_socks_port_automatic(
            self,
            mock_common_log,
            platform_linux):

        onion_obj = Onion()
        onion_obj.settings = Mock()
        onion_obj.settings.get.return_value = 'automatic'

        assert onion_obj.get_tor_socks_port() == ('127.0.0.1', 9150)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'get_tor_socks_port')
        ))
        (onion_obj.
         settings.
         get.
         assert_has_calls((
             call('connection_type'),
             call('connection_type')
         )))

    def test_get_tor_socks_port(
            self,
            mock_common_log,
            platform_linux):

        onion_obj = Onion()
        onion_obj.settings = Mock()
        onion_obj.settings.get.return_value = None

        assert onion_obj.get_tor_socks_port() == (None, None)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'get_tor_socks_port')
        ))
        (onion_obj.
         settings.
         get.
         assert_has_calls((
             call('connection_type'),
             call('connection_type'),
             call('socks_address'),
             call('socks_port')
         )))
