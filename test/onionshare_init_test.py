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
import argparse
import os
import sys
import threading
from unittest.mock import Mock, call

import pytest
import time

import onionshare
from onionshare import (
    main, common, Onion, OnionShare, web, TorErrorInvalidSetting
)


@pytest.fixture
def common_get_version(monkeypatch):
    monkeypatch.setattr(common, 'get_version', lambda: 'DUMMY_VERSION_1.2.3')


@pytest.fixture
def mock_argparse_argument_parser(monkeypatch):
    m = Mock(spec=argparse.ArgumentParser)
    monkeypatch.setattr('argparse.ArgumentParser', m)
    return m


@pytest.fixture
def mock_common_set_debug(monkeypatch):
    m = Mock(spec=common.set_debug)
    monkeypatch.setattr(common, 'set_debug', m)
    return m


@pytest.fixture
def mock_onion(monkeypatch):
    m = Mock(spec=Onion)
    monkeypatch.setattr(onionshare, 'Onion', m)
    return m


@pytest.fixture
def mock_onionshare(monkeypatch):
    m = Mock(spec=OnionShare)
    monkeypatch.setattr(onionshare, 'OnionShare', m)
    return m


@pytest.fixture
def mock_os_access(monkeypatch):
    m = Mock(spec=os.access)
    monkeypatch.setattr('os.access', m)
    return m


@pytest.fixture
def mock_os_chdir(monkeypatch):
    m = Mock(spec=os.chdir)
    monkeypatch.setattr('os.chdir', m)
    return m


@pytest.fixture
def mock_os_path_exists(monkeypatch):
    m = Mock(spec=os.path.exists)
    monkeypatch.setattr('os.path.exists', m)
    return m


@pytest.fixture
def mock_sys_exit(monkeypatch):
    m = Mock(spec=sys.exit)
    monkeypatch.setattr('sys.exit', m)
    return m


@pytest.fixture
def mock_threading_thread(monkeypatch):
    m = Mock(spec=threading.Thread)
    monkeypatch.setattr('threading.Thread', m)
    return m


@pytest.fixture
def mock_time_sleep(monkeypatch):
    m = Mock(spec=time.sleep)
    monkeypatch.setattr('time.sleep', m)
    return m


@pytest.fixture
def mock_web_debug_mode(monkeypatch):
    m = Mock(spec=web.debug_mode)
    monkeypatch.setattr(web, 'debug_mode', m)
    return m


@pytest.fixture
def mock_web_set_file_info(monkeypatch):
    m = Mock(spec=web.set_file_info)
    monkeypatch.setattr(web, 'set_file_info', m)
    return m


@pytest.fixture
def mock_web_stop(monkeypatch):
    m = Mock(spec=web.stop)
    monkeypatch.setattr(web, 'stop', m)
    return m


@pytest.fixture
def sys_argv_filename_only(monkeypatch):
    monkeypatch.setattr('sys.argv', ['', '/TEST_FILENAME.txt'])


@pytest.fixture
def web_slug(monkeypatch):
    monkeypatch.setattr(web, 'slug', 'TEST_SLUG')


@pytest.fixture
def web_start(monkeypatch):
    monkeypatch.setattr(web, 'start', 9999)


@pytest.fixture
def web_zip_filename(monkeypatch):
    monkeypatch.setattr(web, 'zip_filename', '/TEST_FILENAME.txt')


@pytest.fixture
def web_zip_filesize(monkeypatch):
    monkeypatch.setattr(web, 'zip_filesize', 157286400)


class OnionshareTestPause(Exception):
    pass


class TestMain:
    def test_osx_chdir(
            self,
            common_get_version,
            mock_os_chdir,
            platform_darwin,
            sys_onionshare_dev_mode):

        test_path = '/path/to/config.json'
        mock_os_chdir.side_effect = OnionshareTestPause

        try:
            main(test_path)
        except OnionshareTestPause:
            pass

        mock_os_chdir.assert_called_once_with(test_path)

    def test_argparse_arguments(
            self,
            common_get_version,
            mock_argparse_argument_parser,
            platform_linux,
            sys_onionshare_dev_mode):

        (mock_argparse_argument_parser.
         return_value.
         parse_args.
         side_effect) = OnionshareTestPause

        try:
            main()
        except OnionshareTestPause:
            pass

        (mock_argparse_argument_parser.
         return_value.
         add_argument.
         assert_has_calls((
             call('--local-only', action='store_true', dest='local_only', help='Do not attempt to use tor: for development only'),
             call('--stay-open', action='store_true', dest='stay_open', help='Keep onion service running after download has finished'),
             call('--stealth', action='store_true', dest='stealth', help='Create stealth onion service (advanced)'),
             call('--debug', action='store_true', dest='debug', help='Log application errors to stdout, and log web errors to disk'),
             call('--config', default=False, help='Path to a custom JSON config file (optional)', metavar='config'),
             call('filename', help='List of files or folders to share', metavar='filename', nargs='+')
         )))

    def test_parse_args(
            self,
            common_get_version,
            mock_common_set_debug,
            mock_os_access,
            mock_os_path_exists,
            mock_sys_exit,
            mock_web_debug_mode,
            monkeypatch,
            platform_linux,
            sys_onionshare_dev_mode):

        monkeypatch.setattr('sys.argv', [
            'python',
            '--local-only',
            '--stay-open',
            '--stealth',
            '--debug',
            '--config',
            'TEST_CONFIG.json',
            '/TEST_FILENAME.txt'])

        mock_os_access.return_value = False
        mock_os_path_exists.return_value = False
        mock_sys_exit.side_effect = OnionshareTestPause

        try:
            main()
        except OnionshareTestPause:
            pass

        mock_common_set_debug.assert_called_once_with(True)
        mock_web_debug_mode.assert_called_once_with()
        mock_sys_exit.assert_called_once_with()

    def test_onion(
            self,
            common_get_version,
            mock_onion,
            mock_os_access,
            mock_os_path_exists,
            monkeypatch,
            platform_linux,
            sys_argv_filename_only,
            sys_onionshare_dev_mode):

        mock_onion.return_value.connect.side_effect = OnionshareTestPause
        mock_os_access.return_value = True
        mock_os_path_exists.return_value = True

        try:
            main()
        except OnionshareTestPause:
            pass

        (mock_onion.
         return_value.
         connect.
         assert_called_once_with(
             config=False,
             settings=False
         ))

    def test_onion_tor_exception(
            self,
            common_get_version,
            mock_onion,
            mock_os_access,
            mock_os_path_exists,
            mock_sys_exit,
            monkeypatch,
            platform_linux,
            sys_argv_filename_only,
            sys_onionshare_dev_mode):

        tor_test_error_msg = 'Tor test error message'
        (mock_onion.
         return_value.
         connect.
         side_effect) = TorErrorInvalidSetting(tor_test_error_msg)
        mock_os_access.return_value = True
        mock_os_path_exists.return_value = True
        mock_sys_exit.side_effect = OnionshareTestPause

        try:
            main()
        except OnionshareTestPause:
            pass

        (mock_onion.
         return_value.
         connect.
         assert_called_once_with(
             config=False,
             settings=False
         ))
        mock_sys_exit.assert_called_once_with(tor_test_error_msg)

    def test_onion_keyboard_interrupt(
            self,
            common_get_version,
            mock_onion,
            mock_os_access,
            mock_os_path_exists,
            mock_sys_exit,
            monkeypatch,
            platform_linux,
            sys_argv_filename_only,
            sys_onionshare_dev_mode):

        (mock_onion.
         return_value.
         connect.
         side_effect) = KeyboardInterrupt
        mock_os_access.return_value = True
        mock_os_path_exists.return_value = True
        mock_sys_exit.side_effect = OnionshareTestPause

        try:
            main()
        except OnionshareTestPause:
            pass

        (mock_onion.
         return_value.
         connect.
         assert_called_once_with(
             config=False,
             settings=False
         ))

        mock_sys_exit.assert_called_once_with()

    def test_onionshare_keyboard_interrupt(
            self,
            common_get_version,
            mock_onion,
            mock_onionshare,
            mock_os_access,
            mock_os_path_exists,
            mock_sys_exit,
            monkeypatch,
            platform_linux,
            sys_argv_filename_only,
            sys_onionshare_dev_mode):

        (mock_onionshare.
         return_value.
         start_onion_service.
         side_effect) = KeyboardInterrupt
        mock_os_access.return_value = True
        mock_os_path_exists.return_value = True
        mock_sys_exit.side_effect = OnionshareTestPause

        try:
            main()
        except OnionshareTestPause:
            pass

        (mock_onion.
         return_value.
         connect.
         assert_called_once_with(
             config=False,
             settings=False
         ))

        (mock_onionshare.
         return_value.
         set_stealth.
         assert_called_once_with(False))

        (mock_onionshare.
         return_value.
         start_onion_service.
         assert_called_once_with())

        mock_sys_exit.assert_called_once_with()

    def test_service(
            self,
            common_get_version,
            mock_onion,
            mock_onionshare,
            mock_os_access,
            mock_os_path_exists,
            mock_sys_exit,
            mock_threading_thread,
            mock_time_sleep,
            mock_web_set_file_info,
            mock_web_stop,
            monkeypatch,
            platform_linux,
            sys_argv_filename_only,
            sys_onionshare_dev_mode,
            web_start,
            web_slug,
            web_zip_filename,
            web_zip_filesize):

        (mock_onionshare.
         return_value.
         onion_host) = 'TEST_HOST'

        (mock_onionshare.
         return_value.
         port) = 8888

        (mock_onionshare.
         return_value.
         stay_open) = True

        mock_os_access.return_value = True

        mock_os_path_exists.return_value = True

        (mock_threading_thread.
         return_value.
         is_alive.side_effect) = (True, KeyboardInterrupt)

        main()

        # tests
        mock_web_set_file_info.assert_called_once_with(['/TEST_FILENAME.txt'])

        (mock_onionshare.
         return_value.
         cleanup_filenames.
         append.
         assert_called_once_with(web.zip_filename))

        (mock_threading_thread.
         assert_called_once_with(
             target=web.start,
             args=(mock_onionshare.return_value.port,
                   mock_onionshare.return_value.stay_open)
         ))

        assert mock_threading_thread.return_value.daemon is True

        (mock_threading_thread.
         return_value.
         start.
         assert_called_once_with())

        assert (mock_threading_thread.
                return_value.
                is_alive.
                call_count == 2)

        mock_time_sleep.assert_has_calls((call(0.2), call(100)))

        mock_web_stop.assert_called_once_with(
            mock_onionshare.return_value.port)

        (mock_onionshare.
         return_value.
         cleanup.
         assert_called_once_with())

        (mock_onion.
         return_value.
         cleanup.
         assert_called_once_with())

    def test_stealth_service(
            self,
            common_get_version,
            mock_onion,
            mock_onionshare,
            mock_os_access,
            mock_os_path_exists,
            mock_sys_exit,
            mock_threading_thread,
            mock_time_sleep,
            mock_web_set_file_info,
            mock_web_stop,
            monkeypatch,
            platform_linux,
            sys_argv_filename_only,
            sys_onionshare_dev_mode,
            web_start,
            web_slug,
            web_zip_filename,
            web_zip_filesize):
        """
        Exact same test as above except for the `stealth` flag
        """

        monkeypatch.setattr('sys.argv', ['', '--stealth', '/TEST_FILENAME.txt'])

        (mock_onionshare.
         return_value.
         onion_host) = 'TEST_HOST'

        (mock_onionshare.
         return_value.
         port) = 8888

        (mock_onionshare.
         return_value.
         stay_open) = True

        mock_os_access.return_value = True

        mock_os_path_exists.return_value = True

        (mock_threading_thread.
         return_value.
         is_alive.side_effect) = (True, KeyboardInterrupt)

        main()

        # tests
        mock_web_set_file_info.assert_called_once_with(['/TEST_FILENAME.txt'])

        (mock_onionshare.
         return_value.
         cleanup_filenames.
         append.
         assert_called_once_with(web.zip_filename))

        (mock_threading_thread.
         assert_called_once_with(
             target=web.start,
             args=(mock_onionshare.return_value.port,
                   mock_onionshare.return_value.stay_open)
         ))

        assert mock_threading_thread.return_value.daemon is True

        (mock_threading_thread.
         return_value.
         start.
         assert_called_once_with())

        assert (mock_threading_thread.
                return_value.
                is_alive.
                call_count == 2)

        mock_time_sleep.assert_has_calls((call(0.2), call(100)))

        mock_web_stop.assert_called_once_with(
            mock_onionshare.return_value.port)

        (mock_onionshare.
         return_value.
         cleanup.
         assert_called_once_with())

        (mock_onion.
         return_value.
         cleanup.
         assert_called_once_with())
