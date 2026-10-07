import os
import tempfile
from datetime import datetime
from unittest.mock import patch

from PySide6 import QtCore, QtTest

from .gui_base_test import GuiBaseTest
from onionshare.threads import DownloadThread
from onionshare import strings


VALID_SERVICE_ID = "a" * 56


class FakeDownloadResponse:
    def __init__(self, headers=None, chunks=None, fail_after_chunks=None):
        self.headers = headers or {}
        self._chunks = chunks or []
        self._fail_after_chunks = fail_after_chunks

    def iter_content(self, chunk_size=1024):
        sent = 0
        for chunk in self._chunks:
            yield chunk
            sent += 1
            if (
                self._fail_after_chunks is not None
                and sent >= self._fail_after_chunks
            ):
                raise Exception("connection broke")


class TestDownload(GuiBaseTest):
    def new_download_tab(self):
        tab = self.gui.tabs.widget(0)
        self.verify_new_tab(tab)

        tab.download_button.click()
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.download_mode.isVisible())

        # Give the event loop a chance to resolve child widget visibility
        # (e.g. the decorative image), which is pending right after the mode
        # is added to the tab layout
        QtTest.QTest.qWait(500, self.gui.qtapp)

        return tab

    def test_opening_history_hides_decorative_image(self):
        tab = self.new_download_tab()
        mode = tab.download_mode

        self.assertTrue(mode.image.isVisible())
        mode.toggle_history.click()
        self.assertTrue(mode.history.isVisible())
        self.assertFalse(mode.image.isVisible())

        mode.toggle_history.click()
        self.assertFalse(mode.history.isVisible())
        self.assertTrue(mode.image.isVisible())

        self.close_all_tabs()

    def test_download_mode_normalizes_and_rejects_urls(self):
        tab = self.new_download_tab()
        mode = tab.download_mode

        self.assertEqual(
            mode.normalize_onionshare_url(f"{VALID_SERVICE_ID}.onion"),
            (VALID_SERVICE_ID, f"http://{VALID_SERVICE_ID}.onion"),
        )
        self.assertEqual(
            mode.normalize_onionshare_url(
                f"http://{VALID_SERVICE_ID}.onion/some/path?ignored=1"
            ),
            (VALID_SERVICE_ID, f"http://{VALID_SERVICE_ID}.onion"),
        )

        invalid_urls = [
            "",
            "not a url",
            "https://example.com/foo",
            f"ftp://{VALID_SERVICE_ID}.onion",
            "abc.onion",
            f"http://{VALID_SERVICE_ID}.onion.evil.com",
            f"http://sub.{VALID_SERVICE_ID}.onion",
        ]
        for url in invalid_urls:
            with self.assertRaises(ValueError):
                mode.normalize_onionshare_url(url)

        self.close_all_tabs()

    def test_download_response_rejects_html_error_pages_not_html_files(self):
        tab = self.new_download_tab()
        thread = DownloadThread(tab.download_mode)

        valid_responses = [
            FakeDownloadResponse(
                {
                    "Content-Disposition": 'attachment; filename="share.zip"',
                    "Content-Type": "application/zip",
                }
            ),
            FakeDownloadResponse(
                {
                    "Content-Disposition": 'attachment; filename="page.html"',
                    "Content-Type": "text/html; charset=utf-8",
                }
            ),
            FakeDownloadResponse({"Content-Type": "application/octet-stream"}),
        ]
        for response in valid_responses:
            thread.validate_download_response(response)

        invalid_response = FakeDownloadResponse(
            {"Content-Type": "text/html; charset=utf-8"}
        )
        with self.assertRaises(Exception) as cm:
            thread.validate_download_response(invalid_response)
        self.assertEqual(
            str(cm.exception), strings._("error_download_not_onionshare_share")
        )

        self.close_all_tabs()

    def test_download_filename_is_sanitized(self):
        tab = self.new_download_tab()
        thread = DownloadThread(tab.download_mode)

        self.assertEqual(thread.sanitize_download_filename("../../.bashrc"), "bashrc")
        self.assertEqual(
            thread.sanitize_download_filename("..\\..\\evil.txt"), "evil.txt"
        )
        self.assertEqual(
            thread.get_filename_from_content_disposition(
                {"Content-Disposition": 'attachment; filename="../../.bashrc"'}
            ),
            "bashrc",
        )

        self.close_all_tabs()

    def test_save_share_keeps_malicious_filename_inside_download_dir(self):
        tab = self.new_download_tab()
        mode = tab.download_mode
        thread = DownloadThread(mode)

        with tempfile.TemporaryDirectory() as download_dir:
            mode.settings.set("download", "data_dir", download_dir)
            response = FakeDownloadResponse(chunks=[b"hello", b"world"])

            saved_path = thread.save_share("../../.bashrc", response, 0)
            saved_path_abs = os.path.abspath(saved_path)
            download_dir_abs = os.path.abspath(download_dir)

            self.assertTrue(saved_path_abs.startswith(download_dir_abs + os.sep))
            self.assertEqual(os.path.basename(saved_path), "bashrc")
            with open(saved_path, "rb") as f:
                self.assertEqual(f.read(), b"helloworld")
            self.assertFalse(os.path.exists(f"{saved_path}.part"))

        self.close_all_tabs()

    def test_download_working_button_cancels(self):
        tab = self.new_download_tab()
        mode = tab.download_mode
        canceled = []
        mode.server_status.server_canceled.connect(lambda: canceled.append(True))

        mode.server_status.status = mode.server_status.STATUS_WORKING
        mode.server_status.update()
        mode.server_status.server_button.click()

        self.assertTrue(canceled)
        self.assertTrue(mode.stop_requested)

        self.close_all_tabs()

    def test_save_share_fails_when_download_dir_cannot_be_created(self):
        tab = self.new_download_tab()
        mode = tab.download_mode
        thread = DownloadThread(mode)

        with tempfile.TemporaryDirectory() as download_dir:
            mode.settings.set("download", "data_dir", download_dir)

            # Block creation of the date directory by putting a file in its way
            date_dir = os.path.join(
                download_dir, datetime.now().strftime("%Y-%m-%d")
            )
            with open(date_dir, "w") as f:
                f.write("block")

            response = FakeDownloadResponse(chunks=[b"hello", b"world"])
            with self.assertRaises(Exception) as cm:
                thread.save_share("share.zip", response, 0)

            # The download must not continue into a folder that was never
            # created, and the error should be localized
            self.assertTrue(str(cm.exception).startswith("Could not create"))
            self.assertTrue(date_dir in str(cm.exception))

            # No empty timestamped folder is left behind, other than the
            # deliberate blocker file
            self.assertEqual(os.listdir(download_dir), [os.path.basename(date_dir)])
            self.assertTrue(os.path.isfile(date_dir))

        self.close_all_tabs()

    def test_save_share_removes_empty_dir_when_download_fails(self):
        tab = self.new_download_tab()
        mode = tab.download_mode
        thread = DownloadThread(mode)

        with tempfile.TemporaryDirectory() as download_dir:
            mode.settings.set("download", "data_dir", download_dir)

            # The download fails mid-stream after the folder was created
            response = FakeDownloadResponse(chunks=[b"hello"], fail_after_chunks=1)
            with self.assertRaises(Exception):
                thread.save_share("share.zip", response, 10)

            # No empty timestamped folder should be left behind
            self.assertEqual(os.listdir(download_dir), [])

        self.close_all_tabs()

    def test_tab_cleanup_stops_downloads_and_removes_client_auth(self):
        tab = self.new_download_tab()
        mode = tab.download_mode

        # Simulate a polling download with client auth in progress
        mode.service_id = VALID_SERVICE_ID
        mode.is_polling = True
        mode.client_auth_added = True
        mode.timer = QtCore.QTimer(mode)
        mode.timer.setInterval(60000)
        mode.timer.start()
        mode.download_thread = DownloadThread(mode)

        with patch.object(
            mode.common.gui.onion, "remove_onion_client_auth"
        ) as mock_remove:
            tab.cleanup()

            self.assertFalse(mode.timer.isActive())
            self.assertFalse(mode.is_polling)
            self.assertFalse(mode.download_thread.isRunning())
            mock_remove.assert_called_once_with(VALID_SERVICE_ID)
            self.assertFalse(mode.client_auth_added)

        self.close_all_tabs()
