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

import hmac
import logging
import os
import queue
import socket
from unittest.mock import Mock, call

import pytest

from onionshare import common, web
from test.onionshare_common_test import RANDOM_STR_REGEX, SLUG_REGEX


@pytest.fixture
def mock_abort(monkeypatch):
    m = Mock(spec=web.abort)
    monkeypatch.setattr(web, 'abort', m)
    return m


@pytest.fixture
def mock_app(monkeypatch):
    m = Mock(spec=web.app)
    monkeypatch.setattr(web, 'app', m)
    return m


@pytest.fixture
def mock_common_dir_size(monkeypatch):
    m = Mock(spec=common.dir_size)
    monkeypatch.setattr(common, 'dir_size', m)
    return m


@pytest.fixture
def mock_common_human_readable_filesize(monkeypatch):
    m = Mock(spec=common.human_readable_filesize)
    monkeypatch.setattr(common, 'human_readable_filesize', m)
    return m


@pytest.fixture
def mock_common_zipwriter(monkeypatch):
    m = Mock(spec=common.ZipWriter)
    monkeypatch.setattr(common, 'ZipWriter', m)
    return m


@pytest.fixture
def mock_generate_slug(monkeypatch):
    m = Mock(spec=web.generate_slug)
    monkeypatch.setattr(web, 'generate_slug', m)
    return m


@pytest.fixture
def mock_hmac_compare_digest(monkeypatch):
    m = Mock(spec=hmac.compare_digest)
    monkeypatch.setattr('hmac.compare_digest', m)
    return m


@pytest.fixture
def mock_logging_file_handler(monkeypatch):
    m = Mock(spec=logging.FileHandler)
    monkeypatch.setattr('logging.FileHandler', m)
    return m


@pytest.fixture
def mock_os_path(monkeypatch):
    m = Mock(spec=os.path)
    monkeypatch.setattr('os.path', m)
    return m


@pytest.fixture
def mock_request(monkeypatch):
    m = Mock()
    monkeypatch.setattr(web, 'request', m)
    return m


@pytest.fixture
def mock_set_stay_open(monkeypatch):
    m = Mock(spec=web.set_stay_open)
    monkeypatch.setattr(web, 'set_stay_open', m)
    return m


@pytest.fixture
def mock_socket_socket(monkeypatch):
    m = Mock(spec=socket.socket)
    monkeypatch.setattr('socket.socket', m)
    return m


@pytest.fixture
def mock_web_urlopen(monkeypatch):
    m = Mock(spec=web.urlopen)
    monkeypatch.setattr(web, 'urlopen', m)
    return m


class TestSafeSelectJinjaAutoEscape:
    @pytest.mark.parametrize('test_input,expected', (
        ((None, None), True),
        ((None, 'test.html'), True),
        ((None, 'test.htm'), True),
        ((None, 'test.xml'), True),
        ((None, 'test.xhtml'), True),
        ((None, 'invalid.jpg'), False),
        ((None, 'invalid.js'), False),
        ((None, 'invalid.py'), False),
    ))
    def test_filenames(self, test_input, expected):
        assert web._safe_select_jinja_autoescape(*test_input) is expected

    @pytest.mark.parametrize('test_input', (
        (None, 123),
        (None, lambda: None),
        (None, ()),
        (None, {}),
        (None, [])
    ))
    def test_raises_attribute_error(self, test_input):
        with pytest.raises(AttributeError):
            web._safe_select_jinja_autoescape(*test_input)


class TestDefaultVariables:
    def test_variables(self):
        assert web.file_info == []
        assert web.zip_filename is None
        assert web.zip_filesize is None

        assert web.security_headers == [
            ('Content-Security-Policy',
             'default-src \'self\'; style-src \'unsafe-inline\'; img-src \'self\' data:;'),
            ('X-Frame-Options', 'DENY'),
            ('X-Xss-Protection', '1; mode=block'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Referrer-Policy', 'no-referrer'),
            ('Server', 'OnionShare')
        ]

        assert web.REQUEST_LOAD == 0
        assert web.REQUEST_DOWNLOAD == 1
        assert web.REQUEST_PROGRESS == 2
        assert web.REQUEST_OTHER == 3
        assert web.REQUEST_CANCELED == 4
        assert web.REQUEST_RATE_LIMIT == 5

        assert web.q.empty() is True
        assert web.q.full() is False
        assert web.q.qsize() == 0

        assert web.slug is None

        assert web.download_count == 0
        assert web.error404_count == 0

        assert web.stay_open is False

        assert web.gui_mode is False

        assert web.download_in_progress is False

        assert web.client_cancel is False

        assert bool(RANDOM_STR_REGEX.match(web.shutdown_slug)) is True


class TestSetFileInfo:
    def test_files(
            self,
            mock_common_dir_size,
            mock_common_human_readable_filesize,
            mock_common_zipwriter,
            mock_os_path,
            monkeypatch):

        file_info = zip_filename = zip_filesize = None
        monkeypatch.setattr(web, 'file_info', file_info)
        monkeypatch.setattr(web, 'zip_filename', zip_filename)
        monkeypatch.setattr(web, 'zip_filesize', zip_filesize)

        mock_os_path.basename.side_effect = lambda value: value

        # test files, not directories
        mock_os_path.isfile.return_value = True
        mock_os_path.isdir.return_value = False

        dummy_size = 1024
        dummy_readable_size = '1.0 KiB'
        dummy_zip_filename = 'DUMMY_FILENAME.ZIP'
        filenames = ('test_1.txt', 'test_2.txt')

        mock_os_path.getsize.return_value = dummy_size
        mock_common_human_readable_filesize.return_value = dummy_readable_size
        mock_common_zipwriter.return_value.zip_filename = dummy_zip_filename

        web.set_file_info(filenames, None)

        (mock_common_zipwriter.
         assert_called_once_with(processed_size_callback=None))

        (mock_common_zipwriter.
         return_value.
         add_file.
         assert_has_calls(tuple(call(f) for f in filenames)))

        (mock_common_zipwriter.
         return_value.
         close.
         assert_called_once_with())

        assert web.zip_filename == dummy_zip_filename
        assert web.zip_filesize == dummy_size

    def test_directories(
            self,
            mock_common_dir_size,
            mock_common_human_readable_filesize,
            mock_common_zipwriter,
            mock_os_path,
            monkeypatch):

        file_info = zip_filename = zip_filesize = None
        monkeypatch.setattr(web, 'file_info', file_info)
        monkeypatch.setattr(web, 'zip_filename', zip_filename)
        monkeypatch.setattr(web, 'zip_filesize', zip_filesize)

        mock_os_path.basename.side_effect = lambda value: value

        # test directories, not files
        mock_os_path.isfile.return_value = False
        mock_os_path.isdir.return_value = True

        directory_names = ('dir_1/', 'dir_2/')
        dummy_size = 1024
        dummy_readable_size = '1.0 KiB'
        dummy_zip_filename = 'DUMMY_FILENAME.ZIP'

        mock_os_path.getsize.return_value = dummy_size
        mock_common_human_readable_filesize.return_value = dummy_readable_size
        mock_common_zipwriter.return_value.zip_filename = dummy_zip_filename

        web.set_file_info(directory_names, None)

        (mock_common_zipwriter.
         assert_called_once_with(processed_size_callback=None))

        (mock_common_zipwriter.
         return_value.
         add_dir.
         assert_has_calls(tuple(call(f) for f in directory_names)))

        (mock_common_zipwriter.
         return_value.
         close.
         assert_called_once_with())

        assert web.zip_filename == dummy_zip_filename
        assert web.zip_filesize == dummy_size


class TestAddRequest:
    def test_add_to_queue(self, monkeypatch):
        monkeypatch.setattr(web, 'q', queue.Queue())

        one = ('DUMMY_REQUEST_TYPE', 'DUMMY_PATH', 'DUMMY_DATA')
        two = ('DUMMY_REQUEST_TYPE_2', 'DUMMY_PATH_2', 'DUMMY_DATA_2')

        web.add_request(*one)
        web.add_request(*two)

        assert web.q.get() == {
            'type': 'DUMMY_REQUEST_TYPE',
            'path': 'DUMMY_PATH',
            'data': 'DUMMY_DATA'
        }
        assert web.q.get() == {
            'type': 'DUMMY_REQUEST_TYPE_2',
            'path': 'DUMMY_PATH_2',
            'data': 'DUMMY_DATA_2'
        }


class TestGenerateSlug:
    def test_slug(self, monkeypatch, sys_onionshare_dev_mode):
        monkeypatch.setattr(web, 'slug', None)
        assert web.slug is None

        web.generate_slug()

        assert bool(SLUG_REGEX.match(web.slug)) is True


class TestSetStayOpen:
    def test_stay_open_true(self, monkeypatch):
        monkeypatch.setattr(web, 'stay_open', False)
        assert web.stay_open is False

        web.set_stay_open(True)

        assert web.stay_open is True


class TestGetStayOpen:
    def test_get_stay_open(self, monkeypatch):
        monkeypatch.setattr(web, 'stay_open', True)
        assert web.get_stay_open() is True

        web.set_stay_open(False)

        assert web.get_stay_open() is False


class TestSetGuiMode:
    def test_set_gui_mode(self, monkeypatch):
        monkeypatch.setattr(web, 'gui_mode', False)
        assert web.gui_mode is False

        web.set_gui_mode()

        assert web.gui_mode is True


class TestDebugMode:
    def test_debug_windows(
            self,
            mock_app,
            mock_logging_file_handler,
            monkeypatch,
            platform_windows):

        monkeypatch.setenv('Temp', 'C:')

        web.debug_mode()

        # TODO: if `tempfile.gettempdir` is used, this path may change
        # TODO: since (I think?) windows uses forward slashes
        (mock_logging_file_handler.
         assert_called_once_with('C:/onionshare_server.log'))

        (mock_logging_file_handler.
         return_value.
         setLevel.
         assert_called_once_with(logging.WARNING))

        (mock_app.
         logger.
         addHandler.
         called_once_with(mock_logging_file_handler.return_value))

    def test_debug(
            self,
            mock_app,
            mock_logging_file_handler,
            monkeypatch,
            platform_linux):

        web.debug_mode()

        # TODO: double slashes after tmp causes by bug in `web.debug_mode`
        # TODO: if `tempfile.gettempdir` is used, it may have to be mocked
        # TODO: or monkeypatched since it can return different values
        (mock_logging_file_handler.
         assert_called_once_with('/tmp//onionshare_server.log'))

        (mock_logging_file_handler.
         return_value.
         setLevel.
         assert_called_once_with(logging.WARNING))

        (mock_app.
         logger.
         addHandler.
         called_once_with(mock_logging_file_handler.return_value))


class TestCheckSlugCandidate:
    def test_slug_compare_is_none(
            self,
            mock_hmac_compare_digest,
            monkeypatch):

        monkeypatch.setattr(web, 'slug', 'GLOBAL_SLUG')

        web.check_slug_candidate('GLOBAL_SLUG', slug_compare=None)

        (mock_hmac_compare_digest.
         assert_called_once_with('GLOBAL_SLUG', 'GLOBAL_SLUG'))

    def test_slug_compare_is_equal(
            self,
            mock_hmac_compare_digest,
            monkeypatch):

        web.check_slug_candidate('TEST_SLUG', slug_compare='TEST_SLUG')

        (mock_hmac_compare_digest.
         assert_called_once_with('TEST_SLUG', 'TEST_SLUG'))

    def test_slug_compare_not_equal(
            self,
            mock_abort,
            mock_hmac_compare_digest):

        mock_hmac_compare_digest.return_value = False

        web.check_slug_candidate('TEST_SLUG', slug_compare='CUSTOM_SLUG')

        mock_abort.assert_called_once_with(404)

        (mock_hmac_compare_digest.
         assert_called_once_with('CUSTOM_SLUG', 'TEST_SLUG'))


class TestForceShutdown:
    def test_func_is_none(self, mock_request):
        mock_request.environ.get.return_value = None

        with pytest.raises(RuntimeError):
            web.force_shutdown()

            (mock_request.
             environ.
             get.
             assert_called_once_with('werkzeug.server.shutdown'))

    def test_func_is_not_none(self, mock_request):
        web.force_shutdown()

        (mock_request.
         environ.
         get.
         assert_called_once_with('werkzeug.server.shutdown'))

        (mock_request.
         environ.
         get.
         return_value.
         assert_called_once_with())


class TestStart:
    @pytest.mark.parametrize('port,stay_open', (
        (9999, False), (8888, True)
    ))
    def test_whonix(
            self,
            mock_app,
            mock_generate_slug,
            mock_os_path,
            mock_set_stay_open,
            monkeypatch,
            port,
            stay_open):

        mock_os_path.exists.return_value = True
        monkeypatch.setattr('os.path', mock_os_path)

        web.start(port, stay_open)

        mock_generate_slug.assert_called_once_with()

        mock_set_stay_open.assert_called_once_with(stay_open)

        (mock_os_path.
         exists.
         assert_called_once_with('/usr/share/anon-ws-base-files/workstation'))

        (mock_app.
         run.
         assert_called_once_with(
             host='0.0.0.0',
             port=port,
             threaded=True
         ))

    @pytest.mark.parametrize('port,stay_open', (
        (7777, False), (6666, True)
    ))
    def test_no_whonix(
            self,
            mock_app,
            mock_generate_slug,
            mock_os_path,
            mock_set_stay_open,
            monkeypatch,
            port,
            stay_open):

        mock_os_path.exists.return_value = False
        monkeypatch.setattr('os.path', mock_os_path)

        web.start(port, stay_open)

        mock_generate_slug.assert_called_once_with()

        mock_set_stay_open.assert_called_once_with(stay_open)

        (mock_os_path.
         exists.
         assert_called_once_with('/usr/share/anon-ws-base-files/workstation'))

        (mock_app.
         run.
         assert_called_once_with(
             host='127.0.0.1',
             port=port,
             threaded=True
         ))


class TestStop:
    def test_stop(self, mock_socket_socket, monkeypatch):
        port = 9999
        shutdown_slug = 'SHUTDOWN_SLUG'

        monkeypatch.setattr(web, 'client_cancel', False)
        monkeypatch.setattr(web, 'shutdown_slug', shutdown_slug)
        assert web.client_cancel is False

        web.stop(port)

        mock_socket_socket.assert_called_once_with()

        (mock_socket_socket.
         return_value.
         connect.
         assert_called_once_with(
             ('127.0.0.1', port)
         ))

        (mock_socket_socket.
         return_value.
         sendall.
         assert_called_once_with(
            'GET /{}/shutdown HTTP/1.1\r\n\r\n'.format(shutdown_slug)
         ))

    def test_socket_raise_exception(
            self,
            mock_socket_socket,
            mock_web_urlopen,
            monkeypatch):

        port = 8888
        shutdown_slug = 'SHUTDOWN_SLUG'

        mock_socket_socket.side_effect = Exception
        monkeypatch.setattr(web, 'shutdown_slug', shutdown_slug)

        web.stop(port)

        (mock_web_urlopen.
         assert_called_once_with(
             'http://127.0.0.1:{0:d}/{1:s}/shutdown'.format(
                 port, shutdown_slug)
         ))

        (mock_web_urlopen.
         return_value.
         read.
         assert_called_once_with())

    def test_urlopen_raise_exception(
            self,
            mock_socket_socket,
            mock_web_urlopen,
            monkeypatch):

        port = 8888
        shutdown_slug = 'SHUTDOWN_SLUG'

        mock_socket_socket.side_effect = Exception
        mock_web_urlopen.side_effect = Exception
        monkeypatch.setattr(web, 'shutdown_slug', shutdown_slug)

        web.stop(port)

        (mock_web_urlopen.
         assert_called_once_with(
             'http://127.0.0.1:{0:d}/{1:s}/shutdown'.format(
                 port, shutdown_slug)
         ))
