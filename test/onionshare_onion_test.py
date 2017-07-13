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

import os
import subprocess
import tempfile
import textwrap
import time
from unittest.mock import MagicMock, Mock, call, mock_open

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


@pytest.fixture
def mock_time_time(monkeypatch):
    m = Mock(spec=time.time)
    monkeypatch.setattr('time.time', m)
    return m


@pytest.fixture
def mock_onion_controller(monkeypatch):
    m = Mock(spec=onion.Controller)
    monkeypatch.setattr(onion, 'Controller', m)
    return m


@pytest.fixture
def mock_common_get_resource_path(monkeypatch):
    m = Mock(spec=common.get_resource_path)
    monkeypatch.setattr(common, 'get_resource_path', m)
    return m


@pytest.fixture
def mock_common_get_available_port(monkeypatch):
    m = Mock(spec=common.get_available_port)
    monkeypatch.setattr(common, 'get_available_port', m)
    return m


@pytest.fixture
def mock_onion_open(monkeypatch):
    m = mock_open()
    monkeypatch.setattr(onion, 'open', m)
    return m


# @pytest.fixture
# def mock_tempfile_temporary_directory(monkeypatch):
#     m = Mock(spec=tempfile.TemporaryDirectory)
#     monkeypatch.setattr('tempfile.TemporaryDirectory', m)
#     return m


# pytest > 2.9 only needs @pytest.fixture
@pytest.yield_fixture
def temp_torrc_template(monkeypatch):
    """
    Create a temporary file of a particular size (1024 bytes).
    The temporary file will be deleted after fixture usage.
    """

    with tempfile.NamedTemporaryFile('w') as tmp_file:
        tmp_file.write(textwrap.dedent("""\
            DataDirectory {{data_directory}}
            SocksPort {{socks_port}}
            ControlSocket {{control_socket}}
            CookieAuthentication 1
            CookieAuthFile {{cookie_auth_file}}
            AvoidDiskWrites 1
            Log notice stdout
            GeoIPFile {{geo_ip_file}}
            GeoIPv6File {{geo_ipv6_file}}
            """))
        tmp_file.flush()
        yield tmp_file.name


@pytest.fixture
def mock_subprocess_popen(monkeypatch):
    m = Mock(spec=subprocess.Popen)
    monkeypatch.setattr('subprocess.Popen', m)
    return m


@pytest.fixture
def mock_subprocess_startupinfo(monkeypatch):
    m = MagicMock()
    monkeypatch.setattr('subprocess.STARTUPINFO', m, raising=False)
    return m


class TestOnionConnectConnectionTypeAutomatic:
    pass


class TestOnionConnectConnectionTypeBundled:
    def test_no_bundled_tor_support(
            self,
            common_get_tor_paths,
            mock_common_log,
            mock_strings_,
            monkeypatch,
            platform_linux):

        mock_settings = Mock()
        mock_settings.return_value.get.return_value = 'bundled'
        monkeypatch.setattr(onion, 'Settings', mock_settings)
        onion_obj = Onion()
        onion_obj.bundle_tor_supported = False

        with pytest.raises(onion.BundledTorNotSupported):
            onion_obj.connect()
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        mock_settings.assert_called_once_with(False)
        (mock_settings.
         return_value.
         load.
         assert_called_once_with())
        (mock_settings.
         return_value.
         get.
         assert_called_once_with('connection_type'))
        mock_strings_.assert_called_once_with(
            'settings_error_bundled_tor_not_supported')
        assert onion_obj.c is None

    def test_bundled_tor_broken_linux(
            self,
            common_get_tor_paths,
            mock_common_get_available_port,
            mock_common_get_resource_path,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            mock_subprocess_popen,
            mock_time_sleep,
            mock_time_time,
            platform_linux,
            temp_torrc_template):

        test_available_port = 9999
        mock_common_get_available_port.return_value = test_available_port
        mock_common_get_resource_path.return_value = temp_torrc_template
        test_exception_msg = 'Authentication Error!'
        (mock_onion_controller.
         from_socket_file.
         return_value.
         authenticate.
         side_effect) = Exception(test_exception_msg)
        mock_settings = Mock()
        mock_settings.get.return_value = 'bundled'
        onion_obj = Onion()

        with pytest.raises(onion.BundledTorBroken):
            onion_obj.connect(mock_settings)
        mock_common_get_available_port.assert_called_once_with(1000, 65535)
        mock_common_get_resource_path.assert_called_once_with('torrc_template')
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_socket_file.
         assert_called_once_with(
             path=onion_obj.tor_control_socket))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         authenticate.
         assert_called_once_with())
        mock_strings_.assert_called_once_with(
            'settings_error_bundled_tor_broken', True)
        mock_subprocess_popen.assert_called_once_with(
            [onion_obj.tor_path,
             '-f',
             onion_obj.tor_torrc],
            stderr=-1,
            stdout=-1
        )
        mock_time_time.assert_called_once_with()
        mock_time_sleep.assert_called_once_with(2)
        assert onion_obj.tor_control_port is None
        assert onion_obj.tor_control_socket == os.path.join(
            onion_obj.tor_data_directory.name, 'control_socket')
        assert onion_obj.tor_cookie_auth_file == os.path.join(
            onion_obj.tor_data_directory.name, 'cookie')
        assert onion_obj.tor_socks_port == test_available_port
        assert onion_obj.tor_torrc == os.path.join(
            onion_obj.tor_data_directory.name, 'torrc')

        # not needed if added to Onion.cleanup method
        onion_obj.tor_data_directory.cleanup()

    def test_bundled_tor_broken_windows(
            self,
            common_get_tor_paths,
            mock_common_get_available_port,
            mock_common_get_resource_path,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            mock_subprocess_popen,
            mock_subprocess_startupinfo,
            mock_time_sleep,
            mock_time_time,
            monkeypatch,
            platform_windows,
            temp_torrc_template):

        test_tor_control_port = 7777
        test_tor_socks_port = 8888
        test_available_ports = (test_tor_control_port, test_tor_socks_port)
        mock_common_get_available_port.side_effect = test_available_ports
        mock_common_get_resource_path.return_value = temp_torrc_template
        test_exception_msg = 'Authentication Error!'
        (mock_onion_controller.
         from_port.
         return_value.
         authenticate.
         side_effect) = Exception(test_exception_msg)
        mock_settings = Mock()
        mock_settings.get.return_value = 'bundled'
        test_startup_info = 999
        monkeypatch.setattr(
            target=subprocess,
            name='STARTF_USESHOWWINDOW',
            value=test_startup_info,
            raising=False
        )

        onion_obj = Onion()

        with pytest.raises(onion.BundledTorBroken):
            onion_obj.connect(mock_settings)
        mock_common_get_available_port.assert_has_calls((
            call(1000, 65535), call(1000, 65535)
        ))
        (mock_common_get_resource_path.
         assert_called_once_with('torrc_template-windows'))
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_port.
         assert_called_once_with(
             port=onion_obj.tor_control_port))
        (mock_onion_controller.
         from_port.
         return_value.
         authenticate.
         assert_called_once_with())
        mock_strings_.assert_called_once_with(
            'settings_error_bundled_tor_broken', True)
        assert mock_subprocess_popen.call_count == 1
        (mock_subprocess_startupinfo.
         assert_called_once_with())
        mock_time_time.assert_called_once_with()
        mock_time_sleep.assert_called_once_with(2)
        assert onion_obj.tor_control_port == test_tor_control_port
        assert onion_obj.tor_control_socket is None
        assert onion_obj.tor_cookie_auth_file == os.path.join(
            onion_obj.tor_data_directory.name, 'cookie')
        assert onion_obj.tor_socks_port == test_tor_socks_port
        assert onion_obj.tor_torrc == os.path.join(
            onion_obj.tor_data_directory.name, 'torrc')

        # not needed if added to Onion.cleanup method
        onion_obj.tor_data_directory.cleanup()

    def test_bundled_tor_canceled_linux(
            self,
            common_get_tor_paths,
            mock_common_get_available_port,
            mock_common_get_resource_path,
            mock_common_log,
            mock_onion_controller,
            mock_subprocess_popen,
            mock_time_sleep,
            mock_time_time,
            platform_linux,
            temp_torrc_template):

        test_available_port = 9999
        mock_common_get_available_port.return_value = test_available_port
        mock_common_get_resource_path.return_value = temp_torrc_template
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         side_effect) = onion.SocketClosed
        mock_settings = Mock()
        mock_settings.get.return_value = 'bundled'
        onion_obj = Onion()

        with pytest.raises(onion.BundledTorCanceled):
            onion_obj.connect(mock_settings)
        mock_common_get_available_port.assert_called_once_with(1000, 65535)
        mock_common_get_resource_path.assert_called_once_with('torrc_template')
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_socket_file.
         assert_called_once_with(
             path=onion_obj.tor_control_socket))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         authenticate.
         assert_called_once_with())
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         assert_called_once_with('status/bootstrap-phase'))
        mock_subprocess_popen.assert_called_once_with(
            [onion_obj.tor_path,
             '-f',
             onion_obj.tor_torrc],
            stderr=-1,
            stdout=-1
        )
        mock_time_time.assert_called_once_with()
        mock_time_sleep.assert_called_once_with(2)
        assert onion_obj.tor_control_port is None
        assert onion_obj.tor_control_socket == os.path.join(
            onion_obj.tor_data_directory.name, 'control_socket')
        assert onion_obj.tor_cookie_auth_file == os.path.join(
            onion_obj.tor_data_directory.name, 'cookie')
        assert onion_obj.tor_socks_port == test_available_port
        assert onion_obj.tor_torrc == os.path.join(
            onion_obj.tor_data_directory.name, 'torrc')

        # not needed if added to Onion.cleanup method
        onion_obj.tor_data_directory.cleanup()

    def test_bundled_tor_status_update_false_linux(
            self,
            common_get_tor_paths,
            mock_common_get_available_port,
            mock_common_get_resource_path,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            mock_subprocess_popen,
            mock_time_sleep,
            mock_time_time,
            platform_linux,
            temp_torrc_template):

        test_available_port = 9999
        test_progress = 'TEST_PROGRESS'
        test_summary = 'TEST_SUMMARY'
        test_res = '. . .={} . .={}'.format(test_progress, test_summary)
        mock_common_get_available_port.return_value = test_available_port
        mock_common_get_resource_path.return_value = temp_torrc_template
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         return_value) = test_res
        mock_settings = Mock()
        mock_settings.get.return_value = 'bundled'
        onion_obj = Onion()

        assert onion_obj.connect(
            settings=mock_settings,
            tor_status_update_func=lambda progress, summary: False
        ) is False
        mock_common_get_available_port.assert_called_once_with(1000, 65535)
        mock_common_get_resource_path.assert_called_once_with('torrc_template')
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect'),
            call('Onion', 'connect', 'tor_status_update_func returned false, canceling connecting to Tor')
        ))
        (mock_onion_controller.
         from_socket_file.
         assert_called_once_with(
             path=onion_obj.tor_control_socket))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         authenticate.
         assert_called_once_with())
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         assert_called_once_with('status/bootstrap-phase'))
        mock_strings_.assert_called_once_with('connecting_to_tor')
        mock_subprocess_popen.assert_called_once_with(
            [onion_obj.tor_path,
             '-f',
             onion_obj.tor_torrc],
            stderr=-1,
            stdout=-1
        )
        mock_time_time.assert_called_once_with()
        mock_time_sleep.assert_called_once_with(2)
        assert onion_obj.tor_control_port is None
        assert onion_obj.tor_control_socket == os.path.join(
            onion_obj.tor_data_directory.name, 'control_socket')
        assert onion_obj.tor_cookie_auth_file == os.path.join(
            onion_obj.tor_data_directory.name, 'cookie')
        assert onion_obj.tor_socks_port == test_available_port
        assert onion_obj.tor_torrc == os.path.join(
            onion_obj.tor_data_directory.name, 'torrc')

        # not needed if added to Onion.cleanup method
        onion_obj.tor_data_directory.cleanup()

    def test_bundled_tor_timeout_linux(
            self,
            common_get_tor_paths,
            mock_common_get_available_port,
            mock_common_get_resource_path,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            mock_subprocess_popen,
            mock_time_sleep,
            mock_time_time,
            platform_linux,
            temp_torrc_template):

        test_available_port = 9999
        test_progress = 'TEST_PROGRESS'
        test_summary = 'TEST_SUMMARY'
        test_res = '. . .={} . .={}'.format(test_progress, test_summary)
        mock_common_get_available_port.return_value = test_available_port
        mock_common_get_resource_path.return_value = temp_torrc_template
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         return_value) = test_res
        mock_settings = Mock()
        mock_settings.get.return_value = 'bundled'
        mock_time_time.side_effect = (1, 50)
        onion_obj = Onion()

        with pytest.raises(onion.BundledTorTimeout):
            onion_obj.connect(settings=mock_settings)
        mock_common_get_available_port.assert_called_once_with(1000, 65535)
        mock_common_get_resource_path.assert_called_once_with('torrc_template')
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_socket_file.
         assert_called_once_with(
             path=onion_obj.tor_control_socket))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         authenticate.
         assert_called_once_with())
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         assert_called_once_with('status/bootstrap-phase'))
        mock_strings_.assert_has_calls((
            call('connecting_to_tor'),
            call('settings_error_bundled_tor_timeout')
        ))
        mock_subprocess_popen.assert_called_once_with(
            [onion_obj.tor_path, '-f', onion_obj.tor_torrc],
            stderr=-1,
            stdout=-1
        )
        (mock_subprocess_popen.
         return_value.
         terminate.
         assert_called_once_with())
        mock_time_time.assert_has_calls((
            call(),
            call()
        ))
        mock_time_sleep.assert_has_calls((
            call(2),
            call(0.2)
        ))
        assert onion_obj.tor_control_port is None
        assert onion_obj.tor_control_socket == os.path.join(
            onion_obj.tor_data_directory.name, 'control_socket')
        assert onion_obj.tor_cookie_auth_file == os.path.join(
            onion_obj.tor_data_directory.name, 'cookie')
        assert onion_obj.tor_socks_port == test_available_port
        assert onion_obj.tor_torrc == os.path.join(
            onion_obj.tor_data_directory.name, 'torrc')

        # not needed if added to Onion.cleanup method
        onion_obj.tor_data_directory.cleanup()

    def test_bundled_tor_connected_no_stealth_linux(
            self,
            common_get_tor_paths,
            mock_common_get_available_port,
            mock_common_get_resource_path,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            mock_subprocess_popen,
            mock_time_sleep,
            mock_time_time,
            platform_linux,
            temp_torrc_template):

        test_available_port = 9999
        test_progress = 'TEST_PROGRESS'
        test_summary = 'Done'
        test_res = '. . .={} . .={}'.format(test_progress, test_summary)
        test_tor_version = '0.0.0.0'
        mock_common_get_available_port.return_value = test_available_port
        mock_common_get_resource_path.return_value = temp_torrc_template
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         return_value) = test_res
        (mock_onion_controller.
         from_socket_file.
         return_value.
         list_ephemeral_hidden_services) = None
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_version.
         return_value.
         version_str) = test_tor_version
        (mock_onion_controller.
         from_socket_file.
         return_value.
         create_ephemeral_hidden_service.
         side_effect) = Exception
        mock_settings = Mock()
        mock_settings.get.return_value = 'bundled'
        onion_obj = Onion()

        onion_obj.connect(settings=mock_settings)

        mock_common_get_available_port.assert_called_once_with(1000, 65535)
        mock_common_get_resource_path.assert_called_once_with('torrc_template')
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect'),
        ))
        (mock_onion_controller.
         from_socket_file.
         assert_called_once_with(
             path=onion_obj.tor_control_socket))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         authenticate.
         assert_called_once_with())
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         assert_called_once_with('status/bootstrap-phase'))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         create_ephemeral_hidden_service.
         assert_called_once_with(
            {1: 1},
            basic_auth={'onionshare': None},
            await_publication=False
        ))
        mock_strings_.assert_called_once_with('connecting_to_tor')
        mock_subprocess_popen.assert_called_once_with(
            [onion_obj.tor_path, '-f', onion_obj.tor_torrc],
            stderr=-1,
            stdout=-1
        )
        mock_time_time.assert_called_once_with()
        mock_time_sleep.assert_called_once_with(2)
        assert onion_obj.tor_control_port is None
        assert onion_obj.tor_control_socket == os.path.join(
            onion_obj.tor_data_directory.name, 'control_socket')
        assert onion_obj.tor_cookie_auth_file == os.path.join(
            onion_obj.tor_data_directory.name, 'cookie')
        assert onion_obj.tor_socks_port == test_available_port
        assert onion_obj.tor_torrc == os.path.join(
            onion_obj.tor_data_directory.name, 'torrc')
        # If we made it this far, we should be connected to Tor
        assert onion_obj.connected_to_tor is True
        assert onion_obj.tor_version == test_tor_version
        assert onion_obj.supports_ephemeral is False
        assert onion_obj.supports_stealth is False

        # not needed if added to Onion.cleanup method
        onion_obj.tor_data_directory.cleanup()

    def test_bundled_tor_connected_supports_stealth_linux(
            self,
            common_get_tor_paths,
            mock_common_get_available_port,
            mock_common_get_resource_path,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            mock_subprocess_popen,
            mock_time_sleep,
            mock_time_time,
            platform_linux,
            temp_torrc_template):

        test_available_port = 9999
        test_progress = 'TEST_PROGRESS'
        test_service_id = 'TEST_SERVICE_ID'
        test_summary = 'Done'
        test_res = '. . .={} . .={}'.format(test_progress, test_summary)
        test_tor_version = '0.0.0.0'
        mock_common_get_available_port.return_value = test_available_port
        mock_common_get_resource_path.return_value = temp_torrc_template
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         return_value) = test_res
        (mock_onion_controller.
         from_socket_file.
         return_value.
         list_ephemeral_hidden_services) = None
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_version.
         return_value.
         version_str) = test_tor_version
        (mock_onion_controller.
         from_socket_file.
         return_value.
         create_ephemeral_hidden_service.
         return_value.
         content.
         return_value) = (('', '', '={}'.format(test_service_id)),)
        mock_settings = Mock()
        mock_settings.get.return_value = 'bundled'
        onion_obj = Onion()

        onion_obj.connect(settings=mock_settings)

        mock_common_get_available_port.assert_called_once_with(1000, 65535)
        mock_common_get_resource_path.assert_called_once_with('torrc_template')
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect'),
        ))
        (mock_onion_controller.
         from_socket_file.
         assert_called_once_with(
             path=onion_obj.tor_control_socket))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         authenticate.
         assert_called_once_with())
        (mock_onion_controller.
         from_socket_file.
         return_value.
         get_info.
         assert_called_once_with('status/bootstrap-phase'))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         create_ephemeral_hidden_service.
         assert_called_once_with(
            {1: 1},
            basic_auth={'onionshare': None},
            await_publication=False
        ))
        (mock_onion_controller.
         from_socket_file.
         return_value.
         remove_ephemeral_hidden_service.
         assert_called_once_with(
             test_service_id
         ))
        mock_strings_.assert_called_once_with('connecting_to_tor')
        mock_subprocess_popen.assert_called_once_with(
            [onion_obj.tor_path, '-f', onion_obj.tor_torrc],
            stderr=-1,
            stdout=-1
        )
        mock_time_sleep.assert_called_once_with(2)
        mock_time_time.assert_called_once_with()
        assert onion_obj.tor_control_port is None
        assert onion_obj.tor_control_socket == os.path.join(
            onion_obj.tor_data_directory.name, 'control_socket')
        assert onion_obj.tor_cookie_auth_file == os.path.join(
            onion_obj.tor_data_directory.name, 'cookie')
        assert onion_obj.tor_socks_port == test_available_port
        assert onion_obj.tor_torrc == os.path.join(
            onion_obj.tor_data_directory.name, 'torrc')
        # If we made it this far, we should be connected to Tor
        assert onion_obj.connected_to_tor is True
        assert onion_obj.tor_version == test_tor_version
        assert onion_obj.supports_ephemeral is False
        assert onion_obj.supports_stealth is True

        # not needed if added to Onion.cleanup method
        onion_obj.tor_data_directory.cleanup()


class TestOnionConnectConnectionTypeElse:
    # Try connecting
    def test_connection_type_else_raises_socket_file(
            self,
            common_get_tor_paths,
            mock_common_log,
            mock_strings_,
            platform_linux):

        onion_obj = Onion()
        mock_settings = Mock()

        with pytest.raises(onion.TorErrorSocketFile):
            onion_obj.connect(mock_settings)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        mock_settings.assert_has_calls((
            call.get('connection_type'),
            call.get('connection_type'),
            call.get('connection_type'),
            call.get('connection_type'),
            call.get('connection_type'),
            call.get('socket_file_path')
        ))
        mock_strings_.assert_has_calls((
            call('settings_error_unknown'),
            call('settings_error_socket_file')
        ))

    def test_connection_type_control_port_raises_socket_port(
            self,
            common_get_tor_paths,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            platform_linux):

        onion_obj = Onion()
        mock_settings = Mock()
        mock_settings.get.return_value = 'control_port'
        mock_onion_controller.from_port.side_effect = Exception

        with pytest.raises(onion.TorErrorSocketPort):
            onion_obj.connect(mock_settings)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_port.
         assert_called_once_with(
             address='control_port',
             port='control_port'
         ))
        mock_settings.get.assert_has_calls((
            call('connection_type'),
            call('connection_type'),
            call('connection_type'),
            call('control_port_address'),
            call('control_port_port'),
            call('connection_type'),
            call('control_port_address'),
            call('control_port_port')
        ))
        mock_strings_.assert_called_once_with('settings_error_socket_port')

    def test_connection_type_socket_file_raises_socket_file(
            self,
            common_get_tor_paths,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            platform_linux):

        onion_obj = Onion()
        mock_settings = Mock()
        (mock_settings.
         get.
         return_value) = 'socket_file'
        (mock_onion_controller.
         from_socket_file.
         side_effect) = Exception

        with pytest.raises(onion.TorErrorSocketFile):
            onion_obj.connect(mock_settings)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_socket_file.
         assert_called_once_with(path='socket_file'))
        mock_settings.get.assert_has_calls((
            call('connection_type'),
            call('connection_type'),
            call('connection_type'),
            call('connection_type'),
            call('socket_file_path'),
            call('connection_type'),
            call('socket_file_path')
        ))
        mock_strings_.assert_called_once_with('settings_error_socket_file')

    # Try authenticating
    def test_auth_type_no_auth_raises_missing_password(
            self,
            common_get_tor_paths,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            platform_linux):
        onion_obj = Onion()
        mock_settings = Mock()
        (mock_settings.
         get.
         side_effect) = (
            'NOT_BUNDLED',
            'NOT_AUTOMATIC',
            'control_port',
            'control_port_address',
            'control_port_port',
            'no_auth'
        )
        (mock_onion_controller.
         from_port.
         return_value.
         authenticate.
         side_effect) = onion.MissingPassword('Missing Password')

        with pytest.raises(onion.TorErrorMissingPassword):
            onion_obj.connect(mock_settings)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_port.
         return_value.
         authenticate.
         assert_called_once_with())
        (mock_settings.
         get.
         assert_has_calls((
             call('connection_type'),
             call('connection_type'),
             call('connection_type'),
             call('control_port_address'),
             call('control_port_port'),
             call('auth_type')
         )))
        mock_strings_.assert_called_once_with(
            'settings_error_missing_password')

    def test_auth_type_password_raises_unreadable_cookie(
            self,
            common_get_tor_paths,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            platform_linux):
        onion_obj = Onion()
        mock_settings = Mock()
        mock_settings.get.side_effect = (
            'NOT_BUNDLED',
            'NOT_AUTOMATIC',
            'control_port',
            'control_port_address',
            'control_port_port',
            'NOT_NO_AUTH',
            'password',
            'auth_password'
        )
        (mock_onion_controller.
         from_port.
         return_value.
         authenticate.
         side_effect) = onion.UnreadableCookieFile(
            'Unreadable Cookie File', '/', False)

        with pytest.raises(onion.TorErrorUnreadableCookieFile):
            onion_obj.connect(mock_settings)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_port.
         return_value.
         authenticate.
         assert_called_once_with('auth_password'))
        (mock_settings.
         get.
         assert_has_calls((
             call('connection_type'),
             call('connection_type'),
             call('connection_type'),
             call('control_port_address'),
             call('control_port_port'),
             call('auth_type'),
             call('auth_type'),
             call('auth_password')
         )))
        mock_strings_.assert_called_once_with(
            'settings_error_unreadable_cookie_file')

    def test_auth_type_password_raises_auth_error(
            self,
            common_get_tor_paths,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            platform_linux):
        onion_obj = Onion()
        mock_settings = Mock()
        mock_settings.get.side_effect = (
            'NOT_BUNDLED',
            'NOT_AUTOMATIC',
            'control_port',
            'control_port_address',
            'control_port_port',
            'NOT_NO_AUTH',
            'password',
            'auth_password',
            'control_port_address',
            'control_port_port'
        )
        (mock_onion_controller.
         from_port.
         return_value.
         authenticate.
         side_effect) = onion.AuthenticationFailure('Authentication Failure')

        with pytest.raises(onion.TorErrorAuthError):
            onion_obj.connect(mock_settings)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_onion_controller.
         from_port.
         return_value.
         authenticate.
         assert_called_once_with('auth_password'))
        (mock_settings.
         get.
         assert_has_calls((
             call('connection_type'),
             call('connection_type'),
             call('connection_type'),
             call('control_port_address'),
             call('control_port_port'),
             call('auth_type'),
             call('auth_type'),
             call('auth_password')
         )))
        mock_strings_.assert_called_once_with('settings_error_auth')


    def test_auth_type_else_raises_invalid_setting(
            self,
            common_get_tor_paths,
            mock_common_log,
            mock_onion_controller,
            mock_strings_,
            platform_linux):
        onion_obj = Onion()
        mock_settings = Mock()
        mock_settings.get.side_effect = (
            'NOT_BUNDLED',
            'NOT_AUTOMATIC',
            'control_port',
            'control_port_address',
            'control_port_port',
            'NOT_NO_AUTH',
            'NOT_PASSWORD',
        )

        with pytest.raises(onion.TorErrorInvalidSetting):
            onion_obj.connect(mock_settings)
        mock_common_log.assert_has_calls((
            call('Onion', '__init__'),
            call('Onion', 'connect')
        ))
        (mock_settings.
         get.
         assert_has_calls((
             call('connection_type'),
             call('connection_type'),
             call('connection_type'),
             call('control_port_address'),
             call('control_port_port'),
             call('auth_type'),
             call('auth_type'),
         )))
        mock_strings_.assert_called_once_with('settings_error_unknown')


class TestOnionInit:
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


class TestOnionStartOnionService:
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


class TestOnionCleanup:
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


class TestOnionGetTorSocksPort:
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
