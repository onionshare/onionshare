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

import contextlib
import inspect
import io
import os
import random
import re
import socket
import sys
import tempfile
import zipfile

import pytest
import shutil

from onionshare import common

DEFAULT_ZW_FILENAME_REGEX = re.compile(r'^onionshare_[a-z2-7]{6}.zip$')
LOG_MSG_REGEX = re.compile(r"""
    ^\[Jun\ 06\ 2013\ 11:05:00\]
    \ TestModule\.<function\ TestLog\.test_output\.<locals>\.dummy_func
    \ at\ 0x[a-f0-9]+>(:\ TEST_MSG)?$""", re.VERBOSE)
RANDOM_STR_REGEX = re.compile(r'^[a-z2-7]+$')
SLUG_REGEX = re.compile(r'^([a-z]+)(-[a-z]+)?-([a-z]+)(-[a-z]+)?$')


# #################################################
# FIXTURES
# #################################################

# TODO: separate fixtures into a separate file: conftest.py ?
# TODO: comment fixtures properly


@pytest.yield_fixture()
def temp_dir_1024_delete():
    """
    Create a temporary directory that has a single file of a particular
    size (1024 bytes). The temporary directory (and file inside) will
    be deleted after fixture usage.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file, tmp_file_path = tempfile.mkstemp(dir=tmp_dir)
        with open(tmp_file, 'wb') as f:
            f.write(b'*' * 1024)
        yield tmp_dir


@pytest.yield_fixture()
def temp_file_1024_delete():
    """
    Create a temporary file of a particular size (1024 bytes).
    The temporary file will be deleted after fixture usage.
    """

    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(b'*' * 1024)
        tmp_file.flush()
        yield tmp_file.name


# pytest > 2.9 only needs @pytest.fixture
@pytest.yield_fixture(scope='session')
def custom_zw():
    zw = common.ZipWriter(
        zip_filename=common.random_string(4, 6),
        processed_size_callback=lambda _: 'custom_callback'
    )
    yield zw
    zw.close()
    os.remove(zw.zip_filename)


# pytest > 2.9 only needs @pytest.fixture
@pytest.yield_fixture(scope='session')
def default_zw():
    zw = common.ZipWriter()
    yield zw
    zw.close()
    tmp_dir = os.path.dirname(zw.zip_filename)
    shutil.rmtree(tmp_dir)


@pytest.fixture
def platform_darwin(monkeypatch):
    monkeypatch.setattr('platform.system', lambda: 'Darwin')


@pytest.fixture
def platform_linux(monkeypatch):
    monkeypatch.setattr('platform.system', lambda: 'Linux')


@pytest.fixture
def platform_windows(monkeypatch):
    monkeypatch.setattr('platform.system', lambda: 'Windows')


@pytest.fixture
def set_debug_false(monkeypatch):
    monkeypatch.setattr('onionshare.common.debug', False)


@pytest.fixture
def set_debug_true(monkeypatch):
    monkeypatch.setattr('onionshare.common.debug', True)


@pytest.fixture
def sys_argv_sys_prefix(monkeypatch):
    monkeypatch.setattr('sys.argv', [sys.prefix])


@pytest.fixture
def sys_frozen(monkeypatch):
    monkeypatch.setattr('sys.frozen', True, raising=False)


@pytest.fixture
def sys_meipass(monkeypatch):
    monkeypatch.setattr(
        'sys._MEIPASS', os.path.expanduser('~'), raising=False)


@pytest.fixture
def sys_onionshare_dev_mode(monkeypatch):
    monkeypatch.setattr('sys.onionshare_dev_mode', True, raising=False)


@pytest.fixture
def time_time_100(monkeypatch):
    monkeypatch.setattr('time.time', lambda: 100)


@pytest.fixture
def time_strftime(monkeypatch):
    monkeypatch.setattr('time.strftime', lambda _: 'Jun 06 2013 11:05:00')


# #################################################
# TESTS
# #################################################


class TestBuildSlug:
    @pytest.mark.parametrize('test_input,expected', (
        # VALID, two lowercase words, separated by a hyphen
        ('syrup-enzyme', True),
        ('caution-friday', True),

        # VALID, two lowercase words, with one hyphenated compound word
        ('drop-down-thimble', True),
        ('unmixed-yo-yo', True),

        # VALID, two lowercase hyphenated compound words, separated by hyphen
        ('yo-yo-drop-down', True),
        ('felt-tip-t-shirt', True),
        ('hello-world', True),

        # INVALID
        ('Upper-Case', False),
        ('digits-123', False),
        ('too-many-hyphens-', False),
        ('symbols-!@#$%', False)
    ))
    def test_build_slug_regex(self, test_input, expected):
        """ Test that `SLUG_REGEX` accounts for the following patterns

        There are a few hyphenated words in `wordlist.txt`:
            * drop-down
            * felt-tip
            * t-shirt
            * yo-yo

        These words cause a few extra potential slug patterns:
            * word-word
            * hyphenated-word-word
            * word-hyphenated-word
            * hyphenated-word-hyphenated-word
        """

        assert bool(SLUG_REGEX.match(test_input)) == expected

    def test_build_slug_unique(self, sys_onionshare_dev_mode):
        assert common.build_slug() != common.build_slug()


class TestDirSize:
    def test_temp_dir_size(self, temp_dir_1024_delete):
        """ dir_size() should return the total size (in bytes) of all files
        in a particular directory.
        """

        assert common.dir_size(temp_dir_1024_delete) == 1024


class TestEstimatedTimeRemaining:
    @pytest.mark.parametrize('test_input,expected', (
        ((2, 676, 12), '8h14m16s'),
        ((14, 1049, 30), '1h26m15s'),
        ((21, 450, 1), '33m42s'),
        ((31, 1115, 80), '11m39s'),
        ((336, 989, 32), '2m12s'),
        ((603, 949, 38), '36s'),
        ((971, 1009, 83), '1s')
    ))
    def test_estimated_time_remaining(self, test_input, expected, time_time_100):
        assert common.estimated_time_remaining(*test_input) == expected

    @pytest.mark.parametrize('test_input', (
        (10, 20, 100),  # if `time_elapsed == 0`
        (0, 37, 99)     # if `download_rate == 0`
    ))
    def test_raises_zero_division_error(self, test_input, time_time_100):
        with pytest.raises(ZeroDivisionError):
            common.estimated_time_remaining(*test_input)


class TestFormatSeconds:
    @pytest.mark.parametrize('test_input,expected', [
    (0, '0s'),
    (26, '26s'),
    (60, '1m'),
    (947.35, '15m47s'),
    (1847, '30m47s'),
    (2193.94, '36m34s'),
    (3600, '1h'),
    (13426.83, '3h43m47s'),
    (16293, '4h31m33s'),
    (18392.14, '5h6m32s'),
    (86400, '1d'),
    (129674, '1d12h1m14s'),
    (56404.12, '15h40m4s'),
])
    def test_format_seconds(self, test_input, expected):
        assert common.format_seconds(test_input) == expected

    # TODO: test negative numbers?
    @pytest.mark.parametrize('test_input', (
        'string', lambda: None, [], {}, set()
    ))
    def test_invalid_input_types(self, test_input):
        with pytest.raises(TypeError):
            common.format_seconds(test_input)


class TestGetAvailablePort:
    @pytest.mark.parametrize('port_min,port_max', (
        (random.randint(1024, 1500),
         random.randint(1800, 2048)) for _ in range(50)
    ))
    def test_returns_an_open_port(self, port_min, port_max):
        """ get_available_port() should return an open port within the range """

        port = common.get_available_port(port_min, port_max)
        assert port_min <= port <= port_max
        with socket.socket() as tmpsock:
            tmpsock.bind(('127.0.0.1', port))


class TestGetPlatform:
    def test_darwin(self, platform_darwin):
        assert common.get_platform() == 'Darwin'

    def test_linux(self, platform_linux):
        assert common.get_platform() == 'Linux'

    def test_windows(self, platform_windows):
        assert common.get_platform() == 'Windows'


# TODO: double-check these tests
class TestGetResourcePath:
    def test_onionshare_dev_mode(self, sys_onionshare_dev_mode):
        prefix = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(
                        inspect.getfile(
                            inspect.currentframe())))), 'share')
        assert (
            common.get_resource_path(os.path.join(prefix, 'test_filename')) ==
            os.path.join(prefix, 'test_filename'))

    def test_linux(self, platform_linux, sys_argv_sys_prefix):
        prefix = os.path.join(sys.prefix, 'share/onionshare')
        assert (
            common.get_resource_path(os.path.join(prefix, 'test_filename')) ==
            os.path.join(prefix, 'test_filename'))

    def test_frozen_darwin(self, platform_darwin, sys_frozen, sys_meipass):
        prefix = os.path.join(sys._MEIPASS, 'share')
        assert (
            common.get_resource_path(os.path.join(prefix, 'test_filename')) ==
            os.path.join(prefix, 'test_filename'))

    def test_frozen_windows(self, platform_windows, sys_frozen):
        prefix = os.path.join(os.path.dirname(sys.executable), 'share')
        assert (
            common.get_resource_path(os.path.join(prefix, 'test_filename')) ==
            os.path.join(prefix, 'test_filename'))


class TestGetTorPaths:
    # @pytest.mark.skipif(sys.platform != 'Darwin', reason='requires MacOS') ?
    def test_get_tor_paths_darwin(self, platform_darwin, sys_frozen, sys_meipass):
        base_path = os.path.dirname(os.path.dirname(
            os.path.dirname(common.get_resource_path(''))))
        tor_path = os.path.join(base_path, 'Resources', 'Tor', 'tor')
        tor_geo_ip_file_path = os.path.join(
            base_path, 'Resources', 'Tor', 'geoip')
        tor_geo_ipv6_file_path = os.path.join(
            base_path, 'Resources', 'Tor', 'geoip6')
        assert (common.get_tor_paths() ==
                (tor_path, tor_geo_ip_file_path, tor_geo_ipv6_file_path))

    # @pytest.mark.skipif(sys.platform != 'Linux', reason='requires Linux') ?
    def test_get_tor_paths_linux(self, platform_linux):
        assert (common.get_tor_paths() ==
                ('/usr/bin/tor', '/usr/share/tor/geoip', '/usr/share/tor/geoip6'))

    # @pytest.mark.skipif(sys.platform != 'Windows', reason='requires Windows') ?
    def test_get_tor_paths_windows(self, platform_windows, sys_frozen):
        base_path = os.path.join(
            os.path.dirname(os.path.dirname(common.get_resource_path(''))), 'tor')
        tor_path = os.path.join(os.path.join(base_path, 'Tor'), "tor.exe")
        tor_geo_ip_file_path = os.path.join(
            os.path.join(os.path.join(base_path, 'Data'), 'Tor'), 'geoip')
        tor_geo_ipv6_file_path = os.path.join(
            os.path.join(os.path.join(base_path, 'Data'), 'Tor'), 'geoip6')
        assert (common.get_tor_paths() ==
                (tor_path, tor_geo_ip_file_path, tor_geo_ipv6_file_path))


class TestGetVersion:
    def test_get_version(self, sys_onionshare_dev_mode):
        with open(common.get_resource_path('version.txt')) as f:
            version = f.read().strip()

        assert version == common.get_version()


class TestHumanReadableFilesize:
    @pytest.mark.parametrize('test_input,expected', (
        (1024 ** 0, '1.0 B'),
        (1024 ** 1, '1.0 KiB'),
        (1024 ** 2, '1.0 MiB'),
        (1024 ** 3, '1.0 GiB'),
        (1024 ** 4, '1.0 TiB'),
        (1024 ** 5, '1.0 PiB'),
        (1024 ** 6, '1.0 EiB'),
        (1024 ** 7, '1.0 ZiB'),
        (1024 ** 8, '1.0 YiB')
    ))
    def test_human_readable_filesize(self, test_input, expected):
        assert common.human_readable_filesize(test_input) == expected


class TestLog:
    @pytest.mark.parametrize('test_input', (
        ('[Jun 06 2013 11:05:00]'
         ' TestModule.<function TestLog.test_output.<locals>.dummy_func'
         ' at 0xdeadbeef>'),
        ('[Jun 06 2013 11:05:00]'
         ' TestModule.<function TestLog.test_output.<locals>.dummy_func'
         ' at 0xdeadbeef>: TEST_MSG')
    ))
    def test_log_msg_regex(self, test_input):
        assert bool(LOG_MSG_REGEX.match(test_input))

    def test_output(self, set_debug_true, time_strftime):
        def dummy_func():
            pass

        # From: https://stackoverflow.com/questions/1218933
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            common.log('TestModule', dummy_func)
            common.log('TestModule', dummy_func, 'TEST_MSG')
            output = buf.getvalue()

        line_one, line_two, _ = output.split('\n')
        assert LOG_MSG_REGEX.match(line_one)
        assert LOG_MSG_REGEX.match(line_two)


class TestSetDebug:
    def test_debug_true(self, set_debug_false):
        common.set_debug(True)
        assert common.debug is True

    def test_debug_false(self, set_debug_true):
        common.set_debug(False)
        assert common.debug is False


class TestZipWriterDefault:
    @pytest.mark.parametrize('test_input', (
        'onionshare_{}.zip'.format(''.join(
            random.choice('abcdefghijklmnopqrstuvwxyz234567') for _ in range(6))
        ) for _ in range(50)
    ))
    def test_default_zw_filename_regex(self, test_input):
        assert bool(DEFAULT_ZW_FILENAME_REGEX.match(test_input))

    def test_init(self, default_zw):
        pass  # TODO:

    def test_zw_filename(self, default_zw):
        zw_filename = os.path.basename(default_zw.zip_filename)
        assert bool(DEFAULT_ZW_FILENAME_REGEX.match(zw_filename))

    def test_zipfile_filename_matches_zipwriter_filename(self, default_zw):
        assert default_zw.z.filename == default_zw.zip_filename

    def test_zipfile_allow_zip64(self, default_zw):
        assert default_zw.z._allowZip64 is True

    def test_zipfile_mode(self, default_zw):
        assert default_zw.z.mode == 'w'

    def test_callback(self, default_zw):
        assert default_zw.processed_size_callback(None) is None

    def test_add_file(self, default_zw, temp_file_1024_delete):
        default_zw.add_file(temp_file_1024_delete)
        zipfile_info = default_zw.z.getinfo(
            os.path.basename(temp_file_1024_delete))

        assert zipfile_info.compress_type == zipfile.ZIP_DEFLATED
        assert zipfile_info.file_size == 1024

    def test_add_directory(self, temp_dir_1024_delete, default_zw):
        previous_size = default_zw._size  # size before adding directory
        default_zw.add_dir(temp_dir_1024_delete)
        assert default_zw._size == previous_size + 1024


class TestZipWriterCustom:
    @pytest.mark.parametrize('test_input', (
        common.random_string(
            random.randint(2, 50),
            random.choice((None, random.randint(2, 50)))
        ) for _ in range(50)
    ))
    def test_random_string_regex(self, test_input):
        assert bool(RANDOM_STR_REGEX.match(test_input))

    def test_custom_filename(self, custom_zw):
        assert bool(RANDOM_STR_REGEX.match(custom_zw.zip_filename))

    def test_custom_callback(self, custom_zw):
        assert custom_zw.processed_size_callback(None) == 'custom_callback'
