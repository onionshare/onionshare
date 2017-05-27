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
import io
import os
import platform
import random
import re
import shutil
import socket
import tempfile
import time

import pytest

from onionshare import common

LOG_MSG_REGEX = re.compile(r'^\[Jun 06 2013 11:05:00\] TestModule\.<function test_log\.<locals>\.test_func at 0x[a-f0-9]+>(: TEST_MSG)?$')
RANDOM_STR_REGEX = re.compile(r'^[a-z2-7]+$')
SLUG_REGEX = re.compile(r'^([a-z]+)(-[a-z]+)?-([a-z]+)(-[a-z]+)?$')
ZIPWRITER_FILENAME_REGEX = re.compile(r'onionshare_[a-z2-7]{6}.zip$')


# FIXTURES
@pytest.fixture(scope='session')
def custom_zw():
    zw = common.ZipWriter(zip_filename=common.random_string(4, 6))
    yield zw
    zw.close()
    os.remove(zw.zip_filename)


@pytest.fixture(scope='session')
def default_zw():
    zw = common.ZipWriter()
    yield zw
    zw.close()
    os.remove(zw.zip_filename)


@pytest.fixture
def platform_darwin(monkeypatch):
    monkeypatch.setattr(platform, 'system', lambda: 'Darwin')


@pytest.fixture
def platform_linux(monkeypatch):
    monkeypatch.setattr(platform, 'system', lambda: 'Linux')


@pytest.fixture
def platform_windows(monkeypatch):
    monkeypatch.setattr(platform, 'system', lambda: 'Windows')


@pytest.fixture
def time_100(monkeypatch):
    monkeypatch.setattr(time, 'time', lambda: 100)


@pytest.fixture
def time_strftime(monkeypatch):
    monkeypatch.setattr(time, 'strftime', lambda _: 'Jun 06 2013 11:05:00')


# TESTS
@pytest.mark.parametrize('test_input,expected', [
    # VALID, two lowercase words, separated by a hyphen
    ('syrup-enzyme', True),
    ('caution-friday', True),

    # VALID, two lowercase words, with one hyphenated compound word
    ('drop-down-thimble', True),
    ('unmixed-yo-yo', True),

    # VALID, two lowercase hyphenated compound words, separated by a hyphen
    ('yo-yo-drop-down', True),
    ('felt-tip-t-shirt', True),
    ('hello-world', True),

    # INVALID
    ('Upper-Case', False),
    ('digits-123', False),
    ('too-many-hyphens-', False),
    ('symbols-!@#$%', False)
])
def test_build_slug_regex(test_input, expected):
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


def test_build_slug_unique():
    assert common.build_slug() != common.build_slug()


def test_constant_time_compare_different_length_strings():
    assert common.constant_time_compare(
        'test_str'.encode('ascii'), 'test_str_2'.encode('ascii')) is False


def test_constant_time_compare_equal_strings():
    assert common.constant_time_compare(
        'test_str'.encode('ascii'), 'test_str'.encode('ascii')) is True


def test_constant_time_compare_unequal_strings():
    assert common.constant_time_compare(
        'test_str'.encode('ascii'), 'TEST_STR'.encode('ascii')) is False


def test_constant_time_wrong_input_type():
    with pytest.raises(TypeError):
        common.constant_time_compare('test_str', 'test_str'.encode('ascii'))


@pytest.mark.parametrize('directory_size', (5, 500, 5000))
def test_dir_size(directory_size):
    """ dir_size() should return the total size (in bytes) of all files
    in a particular directory.

    This test creates a temporary directory with a single file of a
    particular size. After the test is complete, it deletes the
    temporary directory. 
    """

    tmp_dir = tempfile.mkdtemp()
    with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False) as tmp_file:
        tmp_file.write(b'*' * directory_size)

    # tempfile.TemporaryDirectory raised error when given to `dir_size`
    assert common.dir_size(tmp_dir) == directory_size
    shutil.rmtree(tmp_dir)


@pytest.mark.usefixtures('time_100')
@pytest.mark.parametrize('test_input,expected', (
    ((2, 676, 12), '8h14m16s'),
    ((14, 1049, 30), '1h26m15s'),
    ((21, 450, 1), '33m43s'),
    ((31, 1115, 80), '11m40s'),
    ((336, 989, 32), '2m13s'),
    ((603, 949, 38), '36s'),
    ((971, 1009, 83), '1s')
))
def test_estimated_time_remaining(test_input, expected):
    assert common.estimated_time_remaining(*test_input) == expected


@pytest.mark.usefixtures('time_100')
def test_estimated_time_remaining_time_elapsed_zero():
    """ estimated_time_remaining() raises a ZeroDivisionError if
    `time_elapsed` == 0
    """

    with pytest.raises(ZeroDivisionError):
        common.estimated_time_remaining(10, 20, 100)


@pytest.mark.usefixtures('time_100')
def test_estimated_time_remaining_download_rate_zero():
    """ estimated_time_remaining() raises a ZeroDivision error if
    `download_rate` == 0
    """

    with pytest.raises(ZeroDivisionError):
        common.estimated_time_remaining(0, 37, 99)


@pytest.mark.parametrize('test_input,expected', [
    (0, ''),
    # currently `common.format_seconds` returns '' when given `0`
    # this first test depends if @micahflee approves of change made in #414
    # to `compress.format_seconds` to return '0s' instead of ''
    # (0, '0s'),
    (26, '26s'),
    (60, '1m'),
    (947.35, '15m48s'),
    (1847, '30m47s'),
    (2193.94, '36m34s'),
    (3600, '1h'),
    (13426.83, '3h43m47s'),
    (16293, '4h31m33s'),
    (18392.14, '5h6m33s'),
    (86400, '1d'),
    (18392.14, '5h6m33s'),
    (129674, '1d12h1m14s'),
    (56404.12, '15h40m5s'),
])
def test_format_seconds(test_input, expected):
    assert common.format_seconds(test_input) == expected


def test_get_available_port_returns_an_open_port():
    """ get_available_port() should return an open port within the range """

    for _ in range(100):
        port = common.get_available_port(1024, 2048)
        assert 1024 <= port <= 2048
        with socket.socket() as tmpsock:
            tmpsock.bind(("127.0.0.1", port))


def test_get_platform_returns_platform_system():
    """ get_platform() returns platform.system() when
    ONIONSHARE_PLATFORM is not defined
    """

    p = common.platform.system
    common.platform.system = lambda: 'Sega Saturn'
    assert common.get_platform() == 'Sega Saturn'
    common.platform.system = p


# def test_get_resource_path():
#     pass


# @pytest.mark.skipif(sys.platform != 'Darwin', reason='requires MacOS') ?
@pytest.mark.usefixtures('platform_darwin')
def test_get_tor_paths_darwin():
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
@pytest.mark.usefixtures('platform_linux')
def test_get_tor_paths_linux():
    assert (common.get_tor_paths() ==
            ('/usr/bin/tor', '/usr/share/tor/geoip', '/usr/share/tor/geoip6'))


# @pytest.mark.skipif(sys.platform != 'Windows', reason='requires Windows') ?
@pytest.mark.usefixtures('platform_windows')
def test_get_tor_paths_windows():
    base_path = os.path.join(
        os.path.dirname(os.path.dirname(common.get_resource_path(''))), 'tor')
    tor_path = os.path.join(os.path.join(base_path, 'Tor'), "tor.exe")
    tor_geo_ip_file_path = os.path.join(
        os.path.join(os.path.join(base_path, 'Data'), 'Tor'), 'geoip')
    tor_geo_ipv6_file_path = os.path.join(
        os.path.join(os.path.join(base_path, 'Data'), 'Tor'), 'geoip6')
    assert (common.get_tor_paths() ==
            (tor_path, tor_geo_ip_file_path, tor_geo_ipv6_file_path))


def test_get_version():
    with open(common.get_resource_path('version.txt')) as f:
        version = f.read().strip()

    assert version == common.get_version()


@pytest.mark.parametrize('test_input,expected', [
    (1024 ** 0, '1.0 B'),
    (1024 ** 1, '1.0 KiB'),
    (1024 ** 2, '1.0 MiB'),
    (1024 ** 3, '1.0 GiB'),
    (1024 ** 4, '1.0 TiB'),
    (1024 ** 5, '1.0 PiB'),
    (1024 ** 6, '1.0 EiB'),
    (1024 ** 7, '1.0 ZiB'),
    (1024 ** 8, '1.0 YiB')
])
def test_human_readable_filesize(test_input, expected):
    assert common.human_readable_filesize(test_input) == expected


@pytest.mark.usefixtures('time_strftime')
def test_log():
    def test_func():
        pass

    common.set_debug(True)

    # From: https://stackoverflow.com/questions/1218933
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        common.log('TestModule', test_func)
        common.log('TestModule', test_func, 'TEST_MSG')
        output = buf.getvalue()

    common.set_debug(False)

    line_one, line_two, _ = output.split('\n')
    assert LOG_MSG_REGEX.match(line_one)
    assert LOG_MSG_REGEX.match(line_two)


@pytest.mark.parametrize('test_input,expected', (
    (common.random_string(
        random.randint(2, 50),
        random.choice((None, random.randint(2, 50)))),
     True) for _ in range(50)
))
def test_random_string_regex(test_input, expected):
    assert bool(RANDOM_STR_REGEX.match(test_input)) == expected


def test_set_debug_true():
    common.set_debug(True)
    assert common.debug is True


def test_set_debug_false():
    common.set_debug(False)
    assert common.debug is False


class TestDefaultZipWriter:
    def test_filename(self, default_zw):
        assert bool(ZIPWRITER_FILENAME_REGEX.search(default_zw.zip_filename))

    def test_callback(self, default_zw):
        assert default_zw.processed_size_callback(None) is None

    def test_add_file(self, default_zw):
        file_size = 1000
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b'*' * file_size)
        current_size = default_zw._size
        default_zw.add_file(tmp_file.name)

        assert default_zw._size == current_size + file_size
        os.remove(tmp_file.name)

    def test_add_directory(self, default_zw):
        directory_size = 1000
        tmp_dir = create_temporary_directory(directory_size)
        current_size = default_zw._size
        default_zw.add_dir(tmp_dir)

        assert default_zw._size == current_size + directory_size
        shutil.rmtree(tmp_dir)


def test_zip_writer_custom_filename(custom_zw):
    assert bool(RANDOM_STR_REGEX.match(custom_zw.zip_filename))


def create_temporary_directory(directory_size):
    """ Create a temporary directory with a single file of a
    particular size. Return directory path as a string
    """

    tmp_dir = tempfile.mkdtemp()
    # create_temporary_file(directory=tmp_dir)

    with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False) as tmp_file:
        tmp_file.write(b'*' * directory_size)

    return tmp_dir


# def create_temporary_file(directory=None, delete=False, file_size=100):
#     if file_size <= 0:
#         file_size = 100
#     with tempfile.NamedTemporaryFile(dir=directory, delete=delete) as tmp_file:
#         tmp_file.write(b'*' * file_size)
#     return tmp_file.name
