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

import contextlib
import inspect
import io
import os
import random
import re
import socket
import subprocess
import sys
import time
import zipfile
import tempfile

import pytest

from contextlib import contextmanager
from multiprocessing import Process
from urllib.request import urlopen
from werkzeug.exceptions import RequestedRangeNotSatisfiable

from onionshare.common import Common
from onionshare import strings
from onionshare.web import Web
from onionshare.web.share_mode import parse_range_header
from onionshare.settings import Settings

DEFAULT_ZW_FILENAME_REGEX = re.compile(r'^onionshare_[a-z2-7]{6}.zip$')
RANDOM_STR_REGEX = re.compile(r'^[a-z2-7]+$')


def web_obj(common_obj, mode, num_files=0):
    """ Creates a Web object, in either share mode or receive mode, ready for testing """
    common_obj.load_settings()
    strings.load_strings(common_obj)
    web = Web(common_obj, False, mode)
    web.generate_slug()
    web.stay_open = True
    web.running = True

    web.app.testing = True

    # Share mode
    if mode == 'share':
        # Add files
        files = []
        for i in range(num_files):
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(b'*' * 1024)
                files.append(tmp_file.name)
        web.share_mode.set_file_info(files)
    # Receive mode
    else:
        pass

    return web


class TestWeb:
    def test_share_mode(self, common_obj):
        web = web_obj(common_obj, 'share', 3)
        assert web.mode is 'share'
        with web.app.test_client() as c:
            # Load 404 pages
            res = c.get('/')
            res.get_data()
            assert res.status_code == 404

            res = c.get('/invalidslug'.format(web.slug))
            res.get_data()
            assert res.status_code == 404

            # Load download page
            res = c.get('/{}'.format(web.slug))
            res.get_data()
            assert res.status_code == 200

            # Download
            res = c.get('/{}/download'.format(web.slug))
            res.get_data()
            assert res.status_code == 200
            assert res.mimetype == 'application/zip'

    def test_share_mode_close_after_first_download_on(self, common_obj, temp_file_1024):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = False

        assert web.running == True

        with web.app.test_client() as c:
            # Download the first time
            res = c.get('/{}/download'.format(web.slug))
            res.get_data()
            assert res.status_code == 200
            assert res.mimetype == 'application/zip'

            assert web.running == False

    def test_share_mode_close_after_first_download_off(self, common_obj, temp_file_1024):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True

        assert web.running == True

        with web.app.test_client() as c:
            # Download the first time
            res = c.get('/{}/download'.format(web.slug))
            res.get_data()
            assert res.status_code == 200
            assert res.mimetype == 'application/zip'
            assert web.running == True

    def test_receive_mode(self, common_obj):
        web = web_obj(common_obj, 'receive')
        assert web.mode is 'receive'

        with web.app.test_client() as c:
            # Load 404 pages
            res = c.get('/')
            res.get_data()
            assert res.status_code == 404

            res = c.get('/invalidslug'.format(web.slug))
            res.get_data()
            assert res.status_code == 404

            # Load upload page
            res = c.get('/{}'.format(web.slug))
            res.get_data()
            assert res.status_code == 200

    def test_public_mode_on(self, common_obj):
        web = web_obj(common_obj, 'receive')
        common_obj.settings.set('public_mode', True)

        with web.app.test_client() as c:
            # Upload page should be accessible from /
            res = c.get('/')
            data1 = res.get_data()
            assert res.status_code == 200

            # /[slug] should be a 404
            res = c.get('/{}'.format(web.slug))
            data2 = res.get_data()
            assert res.status_code == 404

    def test_public_mode_off(self, common_obj):
        web = web_obj(common_obj, 'receive')
        common_obj.settings.set('public_mode', False)

        with web.app.test_client() as c:
            # / should be a 404
            res = c.get('/')
            data1 = res.get_data()
            assert res.status_code == 404

            # Upload page should be accessible from /[slug]
            res = c.get('/{}'.format(web.slug))
            data2 = res.get_data()
            assert res.status_code == 200


class TestZipWriterDefault:
    @pytest.mark.parametrize('test_input', (
        'onionshare_{}.zip'.format(''.join(
            random.choice('abcdefghijklmnopqrstuvwxyz234567') for _ in range(6)
        )) for _ in range(50)
    ))
    def test_default_zw_filename_regex(self, test_input):
        assert bool(DEFAULT_ZW_FILENAME_REGEX.match(test_input))

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
        Common.random_string(
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


def check_unsupported(cmd: str, args: list):
    cmd_args = [cmd]
    cmd_args.extend(args)
    skip = False

    try:
        subprocess.check_call(cmd_args)
    except Exception:
        skip = True

    return pytest.mark.skipif(skip, reason='Command {!r} not supported'.format(cmd))


@contextmanager
def live_server(web):
    s = socket.socket()
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()

    def run():
        web.app.run(host='127.0.0.1', port=port, debug=False)

    proc = Process(target=run)
    proc.start()

    url = 'http://127.0.0.1:{}/{}'.format(port, web.slug)

    attempts = 20
    while True:
        try:
            urlopen(url)
            break
        except Exception:
            attempts -= 1
            if attempts > 0:
                time.sleep(0.5)
            else:
                raise

    yield url + '/download'

    proc.terminate()


class TestRangeRequests:

    VALID_RANGES = [
        (None, 500, [(0, 499)]),
        ('bytes=0', 500, [(0, 499)]),
        ('bytes=100', 500, [(100, 499)]),
        ('bytes=100-', 500, [(100, 499)]),  # not in the RFC, but how curl sends
        ('bytes=0-99', 500, [(0, 99)]),
        ('bytes=0-599', 500, [(0, 499)]),
        ('bytes=0-0', 500, [(0, 0)]),
        ('bytes=-100', 500, [(400, 499)]),
        ('bytes=0-99,100-199', 500, [(0, 199)]),
        ('bytes=0-100,100-199', 500, [(0, 199)]),
        ('bytes=0-99,101-199', 500, [(0, 99), (101, 199)]),
        ('bytes=0-199,100-299', 500, [(0, 299)]),
        ('bytes=0-99,200-299', 500, [(0, 99), (200, 299)]),
    ]

    INVALID_RANGES = [
        'bytes=200-100',
        'bytes=0-100,300-200',
    ]

    def test_parse_ranges(self):
        for case in self.VALID_RANGES:
            (header, target_size, expected) = case
            parsed = parse_range_header(header, target_size)
            assert parsed == expected, case

        for invalid in self.INVALID_RANGES:
            with pytest.raises(RequestedRangeNotSatisfiable):
                parse_range_header(invalid, 500)

    def test_headers(self, common_obj):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True
        url = '/{}/download'.format(web.slug)

        with web.app.test_client() as client:
            resp = client.get(url)
            assert resp.headers['ETag'].startswith('"sha256:')
            assert resp.headers['Accept-Ranges'] == 'bytes'
            assert resp.headers.get('Last-Modified') is not None
            assert resp.headers.get('Content-Length') is not None
            assert 'Accept-Encoding' in resp.headers['Vary']

    def test_basic(self, common_obj):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True
        url = '/{}/download'.format(web.slug)
        with open(web.share_mode.download_filename, 'rb') as f:
            contents = f.read()

        with web.app.test_client() as client:
            resp = client.get(url)
            assert resp.status_code == 200
            assert resp.data == contents

    def test_reassemble(self, common_obj):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True
        url = '/{}/download'.format(web.slug)
        with open(web.share_mode.download_filename, 'rb') as f:
            contents = f.read()

        with web.app.test_client() as client:
            resp = client.get(url, headers={'Range': 'bytes=0-10'})
            assert resp.status_code == 206
            content_range = resp.headers['Content-Range']
            assert content_range == 'bytes {}-{}/{}'.format(0, 10, web.share_mode.download_filesize)
            bytes_out = resp.data

            resp = client.get(url, headers={'Range': 'bytes=11-100000'})
            assert resp.status_code == 206
            content_range = resp.headers['Content-Range']
            assert content_range == 'bytes {}-{}/{}'.format(
                11, web.share_mode.download_filesize - 1, web.share_mode.download_filesize)
            bytes_out += resp.data

            assert bytes_out == contents

    def test_mismatched_etags(self, common_obj):
        '''RFC 7233 Section 3.2
           The "If-Range" header field allows a client to "short-circuit" the second request.
           Informally, its meaning is as follows: if the representation is unchanged, send me the
           part(s) that I am requesting in Range; otherwise, send me the entire representation.
        '''
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True
        url = '/{}/download'.format(web.slug)
        with open(web.share_mode.download_filename, 'rb') as f:
            contents = f.read()

        with web.app.test_client() as client:
            resp = client.get(url)
            assert resp.status_code == 200

            resp = client.get(url,
                              headers={'If-Range': 'mismatched etag',
                                       'Range': 'bytes=10-100'})
            assert resp.status_code == 200
            assert resp.data == contents

    def test_if_unmodified_since(self, common_obj):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True
        url = '/{}/download'.format(web.slug)

        with web.app.test_client() as client:
            resp = client.get(url)
            assert resp.status_code == 200
            last_mod = resp.headers['Last-Modified']

            resp = client.get(url, headers={'If-Unmodified-Since': last_mod})
            assert resp.status_code == 304

    @check_unsupported('curl', ['--version'])
    def test_curl(self, common_obj):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True

        with live_server(web) as url:
            # Debugbing help from `man curl`, on error 33
            #       33     HTTP range error. The range "command" didn't work.
            subprocess.check_call(['curl', '--continue-at', '10', url])

    @check_unsupported('wget', ['--version'])
    def test_wget(self, tmpdir, common_obj):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True

        # wget needs a file to exist to continue
        download = tmpdir.join('download')
        download.write('x' * 10)

        with live_server(web) as url:
            subprocess.check_call(['wget', '--continue', '-O', str(download), url])


    @check_unsupported('http', ['--version'])
    def test_httpie(self, common_obj):
        web = web_obj(common_obj, 'share', 3)
        web.stay_open = True

        with live_server(web) as url:
            subprocess.check_call(['http', url, 'Range: bytes=10'])
