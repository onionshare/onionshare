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
import sys
import zipfile
import tempfile

import pytest

from onionshare.common import Common
from onionshare import strings
from onionshare.web import Web
from onionshare.settings import Settings

DEFAULT_ZW_FILENAME_REGEX = re.compile(r'^onionshare_[a-z2-7]{6}.zip$')
RANDOM_STR_REGEX = re.compile(r'^[a-z2-7]+$')


def web_obj(common_obj, mode, num_files=0):
    """ Creates a Web object, in either share mode or receive mode, ready for testing """
    common_obj.settings = Settings(common_obj)
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
