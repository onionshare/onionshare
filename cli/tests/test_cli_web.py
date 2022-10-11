import os
import random
import re
import socket
import subprocess
import time
import zipfile
import tempfile
import base64
import shutil
import sys
from io import BytesIO

import pytest
from contextlib import contextmanager
from multiprocessing import Process
from urllib.request import urlopen, Request
from werkzeug.datastructures import Headers
from werkzeug.exceptions import RequestedRangeNotSatisfiable

from onionshare_cli.common import Common
from onionshare_cli.web import Web
from onionshare_cli.web.share_mode import parse_range_header
from onionshare_cli.settings import Settings
from onionshare_cli.mode_settings import ModeSettings
import onionshare_cli.web.receive_mode

# Stub requests.post, for receive mode webhook tests
webhook_url = None
webhook_data = None


def requests_post_stub(url, data, timeout, proxies):
    global webhook_url, webhook_data
    webhook_url = url
    webhook_data = data


onionshare_cli.web.receive_mode.requests.post = requests_post_stub


DEFAULT_ZW_FILENAME_REGEX = re.compile(r"^onionshare_[a-z2-7]{6}.zip$")
RANDOM_STR_REGEX = re.compile(r"^[a-z2-7]+$")


def web_obj(temp_dir, common_obj, mode, num_files=0):
    """Creates a Web object, in either share mode or receive mode, ready for testing"""
    common_obj.settings = Settings(common_obj)
    mode_settings = ModeSettings(common_obj)
    web = Web(common_obj, False, mode_settings, mode)
    web.running = True

    web.cleanup_tempdirs == []
    web.app.testing = True

    # Share mode
    if mode == "share":
        # Add files
        files = []
        for _ in range(num_files):
            with tempfile.NamedTemporaryFile(
                delete=False, dir=temp_dir.name
            ) as tmp_file:
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
            # Load /
            res = c.get("/")
            res.get_data()
            assert res.status_code == 200

            # Download
            res = c.get("/download")
            res.get_data()
            assert res.status_code == 200
            assert (
                res.mimetype == "application/zip"
                or res.mimetype == "application/x-zip-compressed"
            )

    def test_share_mode_autostop_sharing_on(self, temp_dir, common_obj, temp_file_1024):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", True)

        assert web.running is True

        with web.app.test_client() as c:
            # Download the first time
            res = c.get("/download")
            res.get_data()
            assert res.status_code == 200
            assert (
                res.mimetype == "application/zip"
                or res.mimetype == "application/x-zip-compressed"
            )

            assert web.running is False

    def test_share_mode_autostop_sharing_off(
        self, temp_dir, common_obj, temp_file_1024
    ):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)

        assert web.running is True

        with web.app.test_client() as c:
            # Download the first time
            res = c.get("/download")
            res.get_data()
            assert res.status_code == 200
            assert (
                res.mimetype == "application/zip"
                or res.mimetype == "application/x-zip-compressed"
            )
            assert web.running is True

    def test_receive_mode(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")
        assert web.mode == "receive"

        with web.app.test_client() as c:
            # Load / with valid auth
            res = c.get(
                "/",
            )
            res.get_data()
            assert res.status_code == 200

    def test_receive_mode_webhook(self, temp_dir, common_obj):
        global webhook_url, webhook_data
        webhook_url = None
        webhook_data = None

        web = web_obj(temp_dir, common_obj, "receive")
        assert web.mode == "receive"
        web.settings.set("receive", "webhook_url", "http://127.0.0.1:1337/example")
        web.proxies = None
        assert (
            web.settings.get("receive", "webhook_url")
            == "http://127.0.0.1:1337/example"
        )

        with web.app.test_client() as c:
            res = c.get("/")
            res.get_data()
            assert res.status_code == 200

            res = c.post(
                "/upload-ajax",
                buffered=True,
                content_type="multipart/form-data",
                data={"file[]": (BytesIO(b"THIS IS A TEST FILE"), "new_york.jpg")},
            )
            res.get_data()
            assert res.status_code == 200

            assert webhook_url == "http://127.0.0.1:1337/example"
            assert webhook_data == "1 file submitted to OnionShare"

    def test_receive_mode_message_no_files(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")

        data_dir = os.path.join(temp_dir.name, "OnionShare")
        os.makedirs(data_dir, exist_ok=True)

        web.settings.set("receive", "data_dir", data_dir)

        with web.app.test_client() as c:
            res = c.post(
                "/upload-ajax",
                buffered=True,
                content_type="multipart/form-data",
                data={"text": "you know just sending an anonymous message"},
            )
            content = res.get_data()
            assert res.status_code == 200
            assert b"Message submitted" in content

        # ~/OnionShare should have a folder for the date
        filenames = os.listdir(data_dir)
        assert len(filenames) == 1
        data_dir_date = os.path.join(data_dir, filenames[0])

        # The date folder should have a single message txt file, no folders
        filenames = os.listdir(data_dir_date)
        assert len(filenames) == 1
        assert filenames[0].endswith("-message.txt")

        shutil.rmtree(data_dir)

    def test_receive_mode_message_and_files(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")

        data_dir = os.path.join(temp_dir.name, "OnionShare")
        os.makedirs(data_dir, exist_ok=True)

        web.settings.set("receive", "data_dir", data_dir)

        with web.app.test_client() as c:
            res = c.post(
                "/upload-ajax",
                buffered=True,
                content_type="multipart/form-data",
                data={
                    "file[]": (BytesIO(b"THIS IS A TEST FILE"), "new_york.jpg"),
                    "text": "you know just sending an anonymous message",
                },
            )
            content = res.get_data()
            assert res.status_code == 200
            assert b"Message submitted, uploaded new_york.jpg" in content

        # Date folder should have a time folder with new_york.jpg, and a text message file
        data_dir_date = os.path.join(data_dir, os.listdir(data_dir)[0])
        filenames = os.listdir(data_dir_date)
        assert len(filenames) == 2
        time_str = filenames[0][0:12]
        assert time_str in filenames
        assert f"{time_str}-message.txt" in filenames
        data_dir_time = os.path.join(data_dir_date, time_str)
        assert os.path.isdir(data_dir_time)
        assert os.path.exists(os.path.join(data_dir_time, "new_york.jpg"))

        shutil.rmtree(data_dir)

    def test_receive_mode_files_no_message(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")

        data_dir = os.path.join(temp_dir.name, "OnionShare")
        os.makedirs(data_dir, exist_ok=True)

        web.settings.set("receive", "data_dir", data_dir)

        with web.app.test_client() as c:
            res = c.post(
                "/upload-ajax",
                buffered=True,
                content_type="multipart/form-data",
                data={"file[]": (BytesIO(b"THIS IS A TEST FILE"), "new_york.jpg")},
            )
            content = res.get_data()
            assert res.status_code == 200
            assert b"Uploaded new_york.jpg" in content

        # Date folder should have just a time folder with new_york.jpg
        data_dir_date = os.path.join(data_dir, os.listdir(data_dir)[0])
        filenames = os.listdir(data_dir_date)
        assert len(filenames) == 1
        time_str = filenames[0][0:12]
        assert time_str in filenames
        assert f"{time_str}-message.txt" not in filenames
        data_dir_time = os.path.join(data_dir_date, time_str)
        assert os.path.isdir(data_dir_time)
        assert os.path.exists(os.path.join(data_dir_time, "new_york.jpg"))

        shutil.rmtree(data_dir)

    def test_receive_mode_no_message_no_files(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")

        data_dir = os.path.join(temp_dir.name, "OnionShare")
        os.makedirs(data_dir, exist_ok=True)

        web.settings.set("receive", "data_dir", data_dir)

        with web.app.test_client() as c:
            res = c.post(
                "/upload-ajax",
                buffered=True,
                content_type="multipart/form-data",
                data={},
            )
            content = res.get_data()
            assert res.status_code == 200
            assert b"Nothing submitted" in content

        # Date folder should be empty
        data_dir_date = os.path.join(data_dir, os.listdir(data_dir)[0])
        filenames = os.listdir(data_dir_date)
        assert len(filenames) == 0

        shutil.rmtree(data_dir)

    def test_public_mode_on(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "receive")
        web.settings.set("general", "public", True)

        with web.app.test_client() as c:
            # Loading / should work without auth
            res = c.get("/")
            res.get_data()
            assert res.status_code == 200

    def test_cleanup(self, common_obj, temp_dir_1024):
        web = web_obj(temp_dir_1024, common_obj, "share", 3)

        temp_dir = tempfile.TemporaryDirectory()

        web.cleanup_tempdirs = [temp_dir]
        web.cleanup()

        assert os.path.exists(temp_dir.name) is False

        assert web.cleanup_tempdirs == []


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
        default_zw.add_file(temp_file_1024_delete.name)
        zipfile_info = default_zw.z.getinfo(
            os.path.basename(temp_file_1024_delete.name)
        )

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


def check_unsupported(cmd: str, args: list):
    cmd_args = [cmd]
    cmd_args.extend(args)
    skip = False

    try:
        subprocess.check_call(cmd_args)
    except Exception:
        skip = True

    return pytest.mark.skipif(skip, reason="Command {!r} not supported".format(cmd))


@contextmanager
def live_server(web):
    s = socket.socket()
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()

    def run():
        web.app.run(host="127.0.0.1", port=port, debug=False)

    proc = Process(target=run)
    proc.start()

    url = "http://127.0.0.1:{}".format(port)
    req = Request(url)

    attempts = 20
    while True:
        try:
            urlopen(req)
            break
        except Exception:
            attempts -= 1
            if attempts > 0:
                time.sleep(0.5)
            else:
                raise

    yield url + "/download"

    proc.terminate()


class TestRangeRequests:

    VALID_RANGES = [
        (None, 500, [(0, 499)]),
        ("bytes=0", 500, [(0, 499)]),
        ("bytes=100", 500, [(100, 499)]),
        ("bytes=100-", 500, [(100, 499)]),  # not in the RFC, but how curl sends
        ("bytes=0-99", 500, [(0, 99)]),
        ("bytes=0-599", 500, [(0, 499)]),
        ("bytes=0-0", 500, [(0, 0)]),
        ("bytes=-100", 500, [(400, 499)]),
        ("bytes=0-99,100-199", 500, [(0, 199)]),
        ("bytes=0-100,100-199", 500, [(0, 199)]),
        ("bytes=0-99,101-199", 500, [(0, 99), (101, 199)]),
        ("bytes=0-199,100-299", 500, [(0, 299)]),
        ("bytes=0-99,200-299", 500, [(0, 99), (200, 299)]),
    ]

    INVALID_RANGES = [
        "bytes=200-100",
        "bytes=0-100,300-200",
    ]

    def test_parse_ranges(self):
        for case in self.VALID_RANGES:
            (header, target_size, expected) = case
            parsed = parse_range_header(header, target_size)
            assert parsed == expected, case

        for invalid in self.INVALID_RANGES:
            with pytest.raises(RequestedRangeNotSatisfiable):
                parse_range_header(invalid, 500)

    def test_headers(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)
        url = "/download"

        with web.app.test_client() as client:
            resp = client.get(url)
            assert resp.headers["ETag"].startswith('"sha256:')
            assert resp.headers["Accept-Ranges"] == "bytes"
            assert resp.headers.get("Last-Modified") is not None
            assert resp.headers.get("Content-Length") is not None
            assert "Accept-Encoding" in resp.headers["Vary"]

    def test_basic(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)
        url = "/download"
        with open(web.share_mode.download_filename, "rb") as f:
            contents = f.read()

        with web.app.test_client() as client:
            resp = client.get(url)
            assert resp.status_code == 200
            assert resp.data == contents

    def test_reassemble(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)
        url = "/download"
        with open(web.share_mode.download_filename, "rb") as f:
            contents = f.read()

        with web.app.test_client() as client:
            headers = Headers()
            headers.extend({"Range": "bytes=0-10"})
            resp = client.get(url, headers=headers)
            assert resp.status_code == 206
            content_range = resp.headers["Content-Range"]
            assert content_range == "bytes {}-{}/{}".format(
                0, 10, web.share_mode.download_filesize
            )
            bytes_out = resp.data

            headers.update({"Range": "bytes=11-100000"})
            resp = client.get(url, headers=headers)
            assert resp.status_code == 206
            content_range = resp.headers["Content-Range"]
            assert content_range == "bytes {}-{}/{}".format(
                11,
                web.share_mode.download_filesize - 1,
                web.share_mode.download_filesize,
            )
            bytes_out += resp.data

            assert bytes_out == contents

    def test_mismatched_etags(self, temp_dir, common_obj):
        """RFC 7233 Section 3.2
        The "If-Range" header field allows a client to "short-circuit" the second request.
        Informally, its meaning is as follows: if the representation is unchanged, send me the
        part(s) that I am requesting in Range; otherwise, send me the entire representation.
        """
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)
        url = "/download"
        with open(web.share_mode.download_filename, "rb") as f:
            contents = f.read()

        with web.app.test_client() as client:
            headers = Headers()
            resp = client.get(url, headers=headers)
            assert resp.status_code == 200

            headers.extend({"If-Range": "mismatched etag", "Range": "bytes=10-100"})
            resp = client.get(url, headers=headers)
            assert resp.status_code == 200
            assert resp.data == contents

    def test_if_unmodified_since(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)
        url = "/download"

        with web.app.test_client() as client:
            headers = Headers()
            resp = client.get(url, headers=headers)
            assert resp.status_code == 200
            last_mod = resp.headers["Last-Modified"]

            headers.extend({"If-Unmodified-Since": last_mod})
            resp = client.get(url, headers=headers)
            assert resp.status_code == 304

    def test_firefox_like_behavior(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)
        url = "/download"

        with web.app.test_client() as client:
            headers = Headers()
            resp = client.get(url, headers=headers)
            assert resp.status_code == 200

            # Firefox sends these with all range requests
            etag = resp.headers["ETag"]
            last_mod = resp.headers["Last-Modified"]

            # make a request that uses the full header set
            headers.extend(
                {
                    "Range": "bytes=0-10",
                    "If-Unmodified-Since": last_mod,
                    "If-Range": etag,
                }
            )
            resp = client.get(url, headers=headers)
            assert resp.status_code == 206

    @pytest.mark.skipif(sys.platform != "linux", reason="requires Linux")
    @check_unsupported("curl", ["--version"])
    def test_curl(self, temp_dir, tmpdir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)

        download = tmpdir.join("download")

        with live_server(web) as url:
            # Debugging help from `man curl`, on error 33
            #       33     HTTP range error. The range "command" didn't work.
            subprocess.check_call(
                [
                    "curl",
                    "--output",
                    str(download),
                    "--continue-at",
                    "10",
                    url,
                ]
            )

    @pytest.mark.skipif(sys.platform != "linux", reason="requires Linux")
    @check_unsupported("wget", ["--version"])
    def test_wget(self, temp_dir, tmpdir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)

        # wget needs a file to exist to continue
        download = tmpdir.join("download")
        download.write("x" * 10)

        with live_server(web) as url:
            subprocess.check_call(
                [
                    "wget",
                    "--continue",
                    "-O",
                    str(download),
                    url,
                ]
            )

    @pytest.mark.skipif(sys.platform != "linux", reason="requires Linux")
    @check_unsupported("http", ["--version"])
    def test_httpie(self, temp_dir, common_obj):
        web = web_obj(temp_dir, common_obj, "share", 3)
        web.settings.set("share", "autostop_sharing", False)

        with live_server(web) as url:
            subprocess.check_call(["http", url, "Range: bytes=10"])
