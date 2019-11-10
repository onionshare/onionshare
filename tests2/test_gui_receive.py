import pytest
import os
import requests
from datetime import datetime, timedelta

from PyQt5 import QtCore, QtTest

from .gui_base_test import GuiBaseTest


class TestReceive(GuiBaseTest):
    # Shared test methods

    def upload_file(
        self, tab, file_to_upload, expected_basename, identical_files_at_once=False
    ):
        """Test that we can upload the file"""

        # Wait 2 seconds to make sure the filename, based on timestamp, isn't accidentally reused
        QtTest.QTest.qWait(2000)

        files = {"file[]": open(file_to_upload, "rb")}
        url = f"http://127.0.0.1:{tab.app.port}/upload"
        if tab.settings.get("general", "public"):
            r = requests.post(url, files=files)
            if identical_files_at_once:
                # Send a duplicate upload to test for collisions
                r = requests.post(url, files=files)
        else:
            r = requests.post(
                url,
                files=files,
                auth=requests.auth.HTTPBasicAuth(
                    "onionshare", tab.get_mode().web.password
                ),
            )
            if identical_files_at_once:
                # Send a duplicate upload to test for collisions
                r = requests.post(
                    url,
                    files=files,
                    auth=requests.auth.HTTPBasicAuth(
                        "onionshare", tab.get_mode().web.password
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
                tab.settings.get("receive", "data_dir"), date_dir, time_dir
            )
            expected_filename = os.path.join(receive_mode_dir, expected_basename)
            if os.path.exists(expected_filename):
                exists = True
                break
            now = now - timedelta(seconds=1)

        self.assertTrue(exists)

    def upload_file_should_fail(self, tab):
        """Test that we can't upload the file when permissions are wrong, and expected content is shown"""
        files = {"file[]": open(self.tmpfile_test, "rb")}
        url = f"http://127.0.0.1:{tab.app.port}/upload"
        if tab.settings.get("general", "public"):
            r = requests.post(url, files=files)
        else:
            r = requests.post(
                url,
                files=files,
                auth=requests.auth.HTTPBasicAuth(
                    "onionshare", tab.get_mode().web.password
                ),
            )

        QtCore.QTimer.singleShot(1000, self.accept_dialog)
        self.assertTrue("Error uploading, please inform the OnionShare user" in r.text)

    def upload_dir_permissions(self, mode=0o755):
        """Manipulate the permissions on the upload dir in between tests"""
        os.chmod("/tmp/OnionShare", mode)

    def try_without_auth_in_non_public_mode(self, tab):
        r = requests.post(f"http://127.0.0.1:{tab.app.port}/upload")
        self.assertEqual(r.status_code, 401)
        r = requests.get(f"http://127.0.0.1:{tab.app.port}/close")
        self.assertEqual(r.status_code, 401)

    # 'Grouped' tests follow from here

    def run_all_receive_mode_setup_tests(self, tab):
        """Set up a share in Receive mode and start it"""
        self.history_is_not_visible(tab)
        self.click_toggle_history(tab)
        self.history_is_visible(tab)
        self.server_working_on_start_button_pressed(tab)
        self.server_status_indicator_says_starting(tab)
        self.server_is_started(tab)
        self.web_server_is_running(tab)
        self.have_a_password(tab)
        self.url_description_shown(tab)
        self.have_copy_url_button(tab)
        self.server_status_indicator_says_started(tab)
        self.web_page(tab, "Select the files you want to send, then click")

    def run_all_receive_mode_tests(self, tab):
        """Upload files in receive mode and stop the share"""
        self.run_all_receive_mode_setup_tests(tab)
        if not tab.settings.get("general", "public"):
            self.try_without_auth_in_non_public_mode(tab)
        self.upload_file(tab, self.tmpfile_test, "test.txt")
        self.history_widgets_present(tab)
        self.counter_incremented(tab, 1)
        self.upload_file(tab, self.tmpfile_test, "test.txt")
        self.counter_incremented(tab, 2)
        self.upload_file(tab, self.tmpfile_test2, "test2.txt")
        self.counter_incremented(tab, 3)
        self.upload_file(tab, self.tmpfile_test2, "test2.txt")
        self.counter_incremented(tab, 4)
        # Test uploading the same file twice at the same time, and make sure no collisions
        self.upload_file(tab, self.tmpfile_test, "test.txt", True)
        self.counter_incremented(tab, 6)
        self.history_indicator(tab, "2")
        self.server_is_stopped(tab)
        self.web_server_is_stopped(tab)
        self.server_status_indicator_says_closed(tab)
        self.server_working_on_start_button_pressed(tab)
        self.server_is_started(tab)
        self.history_indicator(tab, "2")

    def run_all_receive_mode_unwritable_dir_tests(self, tab):
        """Attempt to upload (unwritable) files in receive mode and stop the share"""
        self.run_all_receive_mode_setup_tests(tab)
        self.upload_dir_permissions(0o400)
        self.upload_file_should_fail(tab)
        self.server_is_stopped(tab, True)
        self.web_server_is_stopped(tab)
        self.server_status_indicator_says_closed(tab, False)
        self.upload_dir_permissions(0o755)

    def run_all_clear_all_button_tests(self, tab):
        """Test the Clear All history button"""
        self.run_all_receive_mode_setup_tests(tab)
        self.upload_file(tab, self.tmpfile_test, "test.txt")
        self.history_widgets_present(tab)
        self.clear_all_history_items(tab, 0)
        self.upload_file(tab, self.tmpfile_test, "test.txt")
        self.clear_all_history_items(tab, 2)

    # Tests

    @pytest.mark.gui
    def test_clear_all_button(self):
        """
        Clear all history items should work
        """
        tab = self.new_receive_tab()

        self.run_all_common_setup_tests()
        self.run_all_clear_all_button_tests(tab)

        self.close_all_tabs()

    @pytest.mark.gui
    def test_autostop_timer(self):
        """
        Test autostop timer
        """
        tab = self.new_receive_tab()
        tab.get_mode().mode_settings_widget.toggle_advanced_button.click()
        tab.get_mode().mode_settings_widget.autostop_timer_checkbox.click()

        self.run_all_common_setup_tests()
        self.run_all_receive_mode_setup_tests(tab)
        self.set_timeout(tab, 5)
        self.autostop_timer_widget_hidden(tab)
        self.server_timed_out(tab, 15000)
        self.web_server_is_stopped(tab)

        self.close_all_tabs()

    @pytest.mark.gui
    def test_upload(self):
        """
        Test uploading files
        """
        tab = self.new_receive_tab()

        self.run_all_common_setup_tests()
        self.run_all_receive_mode_tests(tab)

        self.close_all_tabs()
