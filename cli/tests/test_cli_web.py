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
import base64

import pytest
from werkzeug.datastructures import Headers

from onionshare_cli.common import Common
from onionshare_cli.web import Web
from onionshare_cli.settings import Settings
from onionshare_cli.mode_settings import ModeSettings

DEFAULT_ZW_FILENAME_REGEX = re.compile(r"^onionshare_[a-z2-7]{6}.zip$")
RANDOM_STR_REGEX = re.compile(r"^[a-z2-7]+$")


def web_obj(temp_dir, common_obj, mode, num_files=0):
    """ Creates a Web object, in either share mode or receive mode, ready for testing """
    common_obj.settings = Settings(common_obj)
    mode_settings = ModeSettings(common_obj)
    web = Web(common_obj, False, mode_settings, mode)
    web.generate_password()
    web.running = True

    web.app.testing = True

    # Share mode
    if mode == "share":
        # Add files
        files = []
        for _ in range(num_files):
            with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir) as tmp_file:
                tmp_file.write(b"*" * 1024)
                files.append(tmp_file.name)
        web.share_mode.set_file_info(files)
    # Receive mode
    else:
        pass

    return web


class TestWeb:
    def test_share_mode(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        assert web.mode == "share"
        with web.app.test_client() as c:
            # Load / without auth
            res = c.get("/")
            res.get_data()
            assert res.status_code == 401

            # Load / with invalid auth
            res = c.get("/", headers=self._make_auth_headers("invalid"))
            res.get_data()
            assert res.status_code == 401

            # Load / with valid auth
            res = c.get("/", headers=self._make_auth_headers(web.password))
            res.get_data()
            assert res.status_code == 200

            # Download
            res = c.get("/download", headers=self._make_auth_headers(web.password))
            res.get_data()
            assert res.status_code == 200
            assert (
                res.mimetype == "application/zip"
                or res.mimetype == "application/x-zip-compressed"
            )

    def test_share_mode_autostop_sharing_on(self, temp_dir, common_obj, temp_file_1024):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", True)

        assert web.running == True

        with web.app.test_client() as c:
            # Download the first time
            res = c.get("/download", headers=self._make_auth_headers(web.password))
            res.get_data()
            assert res.status_code == 200
            assert (
                res.mimetype == "application/zip"
                or res.mimetype == "application/x-zip-compressed"
            )

            assert web.running == False

    def test_share_mode_autostop_sharing_off(
        self, temp_dir, common_obj, temp_file_1024
    ):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)

        assert web.running == True

        with web.app.test_client() as c:
            # Download the first time
            res = c.get("/download", headers=self._make_auth_headers(web.password))
            res.get_data()
            assert res.status_code == 200
            assert (
                res.mimetype == "application/zip"
                or res.mimetype == "application/x-zip-compressed"
            )
            assert web.running == True

    def test_receive_mode(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")
        assert web.mode == "receive"

        with web.app.test_client() as c:
            # Load / without auth
            res = c.get("/")
            res.get_data()
            assert res.status_code == 401

            # Load / with invalid auth
            res = c.get("/", headers=self._make_auth_headers("invalid"))
            res.get_data()
            assert res.status_code == 401

            # Load / with valid auth
            res = c.get("/", headers=self._make_auth_headers(web.password))
            res.get_data()
            assert res.status_code == 200

    def test_public_mode_on(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")
        web.settings.set("general", "public", True)

        with web.app.test_client() as c:
            # Loading / should work without auth
            res = c.get("/")
            data1 = res.get_data()
            assert res.status_code == 200

    def test_public_mode_off(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")
        web.settings.set("general", "public", False)

        with web.app.test_client() as c:
            # Load / without auth
            res = c.get("/")
            res.get_data()
            assert res.status_code == 401

            # But static resources should work without auth
            res = c.get(f"{web.static_url_path}/css/style.css")
            res.get_data()
            assert res.status_code == 200

            # Load / with valid auth
            res = c.get("/", headers=self._make_auth_headers(web.password))
            res.get_data()
            assert res.status_code == 200

    def _make_auth_headers(self, password):
        auth = base64.b64encode(b"onionshare:" + password.encode()).decode()
        h = Headers()
        h.add("Authorization", "Basic " + auth)
        return h


class TestZipWriterDefault:
    @pytest.mark.parametrize(
        "test_input",
        (
            f"onionshare_{''.join(random.choice('abcdefghijklmnopqrstuvwxyz234567') for _ in range(6))}.zip"
            for _ in range(50)
        ),
    )
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
        assert default_zw.z.mode == "w"

    def test_callback(self, default_zw):
        assert default_zw.processed_size_callback(None) is None

    def test_add_file(self, default_zw, temp_file_1024_delete):
        default_zw.add_file(temp_file_1024_delete)
        zipfile_info = default_zw.z.getinfo(os.path.basename(temp_file_1024_delete))

        assert zipfile_info.compress_type == zipfile.ZIP_DEFLATED
        assert zipfile_info.file_size == 1024

    def test_add_directory(self, temp_dir_1024_delete, default_zw):
        previous_size = default_zw._size  # size before adding directory
        default_zw.add_dir(temp_dir_1024_delete)
        assert default_zw._size == previous_size + 1024


class TestZipWriterCustom:
    @pytest.mark.parametrize(
        "test_input",
        (
            Common.random_string(
                random.randint(2, 50), random.choice((None, random.randint(2, 50)))
            )
            for _ in range(50)
        ),
    )
    def test_random_string_regex(self, test_input):
        assert bool(RANDOM_STR_REGEX.match(test_input))

    def test_custom_filename(self, custom_zw):
        assert bool(RANDOM_STR_REGEX.match(custom_zw.zip_filename))

    def test_custom_callback(self, custom_zw):
        assert custom_zw.processed_size_callback(None) == "custom_callback"
