import os
import requests
from datetime import datetime, timedelta
from PyQt5 import QtCore, QtTest
from .GuiBaseTest import GuiBaseTest


class GuiReceiveTest(GuiBaseTest):
    def upload_file(
        self,
        public_mode,
        file_to_upload,
        expected_basename,
        identical_files_at_once=False,
    ):
        """Test that we can upload the file"""

        # Wait 2 seconds to make sure the filename, based on timestamp, isn't accidentally reused
        QtTest.QTest.qWait(2000)

        files = {"file[]": open(file_to_upload, "rb")}
        url = f"http://127.0.0.1:{self.gui.app.port}/upload"
        if public_mode:
            r = requests.post(url, files=files)
            if identical_files_at_once:
                # Send a duplicate upload to test for collisions
                r = requests.post(url, files=files)
        else:
            r = requests.post(
                url,
                files=files,
                auth=requests.auth.HTTPBasicAuth(
                    "onionshare", self.gui.receive_mode.web.password
                ),
            )
            if identical_files_at_once:
                # Send a duplicate upload to test for collisions
                r = requests.post(
                    url,
                    files=files,
                    auth=requests.auth.HTTPBasicAuth(
                        "onionshare", self.gui.receive_mode.web.password
                    ),
                )

        QtTest.QTest.qWait(2000)

        # Make sure the file is within the last 10 seconds worth of fileames
        exists = False
        now = datetime.now()
        for i in range(10):
            date_dir = now.strftime("%Y-%m-%d")
            if identical_files_at_once:
                time_dir = now.strftime("%H.%M.%S-1")
            else:
                time_dir = now.strftime("%H.%M.%S")
            receive_mode_dir = os.path.join(
                self.gui.common.settings.get("data_dir"), date_dir, time_dir
            )
            expected_filename = os.path.join(receive_mode_dir, expected_basename)
            if os.path.exists(expected_filename):
                exists = True
                break
            now = now - timedelta(seconds=1)

        self.assertTrue(exists)

    def upload_file_should_fail(self, public_mode):
        """Test that we can't upload the file when permissions are wrong, and expected content is shown"""
        files = {"file[]": open("/tmp/test.txt", "rb")}
        url = f"http://127.0.0.1:{self.gui.app.port}/upload"
        if public_mode:
            r = requests.post(url, files=files)
        else:
            r = requests.post(
                url,
                files=files,
                auth=requests.auth.HTTPBasicAuth(
                    "onionshare", self.gui.receive_mode.web.password
                ),
            )

        QtCore.QTimer.singleShot(1000, self.accept_dialog)
        self.assertTrue("Error uploading, please inform the OnionShare user" in r.text)

    def upload_dir_permissions(self, mode=0o755):
        """Manipulate the permissions on the upload dir in between tests"""
        os.chmod("/tmp/OnionShare", mode)

    def try_without_auth_in_non_public_mode(self):
        r = requests.post(f"http://127.0.0.1:{self.gui.app.port}/upload")
        self.assertEqual(r.status_code, 401)
        r = requests.get(f"http://127.0.0.1:{self.gui.app.port}/close")
        self.assertEqual(r.status_code, 401)

    # 'Grouped' tests follow from here

    def run_all_receive_mode_setup_tests(self, public_mode):
        """Set up a share in Receive mode and start it"""
        self.click_mode(self.gui.receive_mode)
        self.history_is_not_visible(self.gui.receive_mode)
        self.click_toggle_history(self.gui.receive_mode)
        self.history_is_visible(self.gui.receive_mode)
        self.server_working_on_start_button_pressed(self.gui.receive_mode)
        self.server_status_indicator_says_starting(self.gui.receive_mode)
        self.settings_button_is_hidden()
        self.server_is_started(self.gui.receive_mode)
        self.web_server_is_running()
        self.have_a_password(self.gui.receive_mode, public_mode)
        self.url_description_shown(self.gui.receive_mode)
        self.have_copy_url_button(self.gui.receive_mode, public_mode)
        self.server_status_indicator_says_started(self.gui.receive_mode)
        self.web_page(
            self.gui.receive_mode,
            "Select the files you want to send, then click",
            public_mode,
        )

    def run_all_receive_mode_tests(self, public_mode):
        """Upload files in receive mode and stop the share"""
        self.run_all_receive_mode_setup_tests(public_mode)
        if not public_mode:
            self.try_without_auth_in_non_public_mode()
        self.upload_file(public_mode, "/tmp/test.txt", "test.txt")
        self.history_widgets_present(self.gui.receive_mode)
        self.counter_incremented(self.gui.receive_mode, 1)
        self.upload_file(public_mode, "/tmp/test.txt", "test.txt")
        self.counter_incremented(self.gui.receive_mode, 2)
        self.upload_file(public_mode, "/tmp/testdir/test", "test")
        self.counter_incremented(self.gui.receive_mode, 3)
        self.upload_file(public_mode, "/tmp/testdir/test", "test")
        self.counter_incremented(self.gui.receive_mode, 4)
        # Test uploading the same file twice at the same time, and make sure no collisions
        self.upload_file(public_mode, "/tmp/test.txt", "test.txt", True)
        self.counter_incremented(self.gui.receive_mode, 6)
        self.history_indicator(self.gui.receive_mode, public_mode, "2")
        self.server_is_stopped(self.gui.receive_mode, False)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)
        self.server_working_on_start_button_pressed(self.gui.receive_mode)
        self.server_is_started(self.gui.receive_mode)
        self.history_indicator(self.gui.receive_mode, public_mode, "2")

    def run_all_receive_mode_unwritable_dir_tests(self, public_mode):
        """Attempt to upload (unwritable) files in receive mode and stop the share"""
        self.run_all_receive_mode_setup_tests(public_mode)
        self.upload_dir_permissions(0o400)
        self.upload_file_should_fail(public_mode)
        self.server_is_stopped(self.gui.receive_mode, True)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)
        self.upload_dir_permissions(0o755)

    def run_all_receive_mode_timer_tests(self, public_mode):
        """Auto-stop timer tests in receive mode"""
        self.run_all_receive_mode_setup_tests(public_mode)
        self.set_timeout(self.gui.receive_mode, 5)
        self.autostop_timer_widget_hidden(self.gui.receive_mode)
        self.server_timed_out(self.gui.receive_mode, 15000)
        self.web_server_is_stopped()

    def run_all_clear_all_button_tests(self, public_mode):
        """Test the Clear All history button"""
        self.run_all_receive_mode_setup_tests(public_mode)
        self.upload_file(public_mode, "/tmp/test.txt", "test.txt")
        self.history_widgets_present(self.gui.receive_mode)
        self.clear_all_history_items(self.gui.receive_mode, 0)
        self.upload_file(public_mode, "/tmp/test.txt", "test.txt")
        self.clear_all_history_items(self.gui.receive_mode, 2)
