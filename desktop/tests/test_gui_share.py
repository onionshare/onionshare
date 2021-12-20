import os
import requests
import tempfile
import zipfile

from PySide2 import QtCore, QtTest

from .gui_base_test import GuiBaseTest


class TestShare(GuiBaseTest):
    # Shared test methods

    def removing_all_files_hides_remove_button(self, tab):
        """Test that clicking on the file item shows the remove button. Test that removing the only item in the list hides the remove button"""
        rect = tab.get_mode().server_status.file_selection.file_list.visualItemRect(
            tab.get_mode().server_status.file_selection.file_list.item(0)
        )
        QtTest.QTest.mouseClick(
            tab.get_mode().server_status.file_selection.file_list.viewport(),
            QtCore.Qt.LeftButton,
            pos=rect.center(),
        )
        # Remove button should be visible
        self.assertTrue(
            tab.get_mode().server_status.file_selection.remove_button.isVisible()
        )
        # Click remove, remove button should still be visible since we have one more file
        tab.get_mode().server_status.file_selection.remove_button.click()
        rect = tab.get_mode().server_status.file_selection.file_list.visualItemRect(
            tab.get_mode().server_status.file_selection.file_list.item(0)
        )
        QtTest.QTest.mouseClick(
            tab.get_mode().server_status.file_selection.file_list.viewport(),
            QtCore.Qt.LeftButton,
            pos=rect.center(),
        )
        self.assertTrue(
            tab.get_mode().server_status.file_selection.remove_button.isVisible()
        )
        tab.get_mode().server_status.file_selection.remove_button.click()

        # No more files, the remove button should be hidden
        self.assertFalse(
            tab.get_mode().server_status.file_selection.remove_button.isVisible()
        )

    def add_a_file_and_remove_using_its_remove_widget(self, tab):
        """Test that we can also remove a file by clicking on its [X] widget"""
        num_files = tab.get_mode().server_status.file_selection.get_num_files()
        tab.get_mode().server_status.file_selection.file_list.add_file(self.tmpfiles[0])
        tab.get_mode().server_status.file_selection.file_list.item(
            0
        ).item_button.click()
        self.file_selection_widget_has_files(tab, num_files)

    def add_a_file_and_remove_using_remove_all_widget(self, tab):
        """Test that we can also remove all files by clicking on the Remove All widget"""
        tab.get_mode().server_status.file_selection.file_list.add_file(self.tmpfiles[0])
        tab.get_mode().server_status.file_selection.file_list.add_file(self.tmpfiles[1])
        tab.get_mode().remove_all_button.click()
        # Should be no files after clearing all
        self.file_selection_widget_has_files(tab, 0)

    def file_selection_widget_read_files(self, tab):
        """Re-add some files to the list so we can share"""
        num_files = tab.get_mode().server_status.file_selection.get_num_files()
        tab.get_mode().server_status.file_selection.file_list.add_file(self.tmpfiles[0])
        tab.get_mode().server_status.file_selection.file_list.add_file(self.tmpfiles[1])
        self.file_selection_widget_has_files(tab, num_files + 2)

    def download_share(self, tab):
        """Test that we can download the share"""
        url = f"http://127.0.0.1:{tab.app.port}/download"
        r = requests.get(url)

        tmp_file = tempfile.NamedTemporaryFile("wb", delete=False)
        tmp_file.write(r.content)
        tmp_file.close()

        z = zipfile.ZipFile(tmp_file.name)
        QtTest.QTest.qWait(5, self.gui.qtapp)
        self.assertEqual("onionshare", z.read("test.txt").decode("utf-8"))

        QtTest.QTest.qWait(500, self.gui.qtapp)

    def individual_file_is_viewable_or_not(self, tab):
        """
        Test that an individual file is viewable (when in autostop_sharing is false) or that it
        isn't (when not in autostop_sharing is true)
        """
        url = f"http://127.0.0.1:{tab.app.port}"
        download_file_url = f"http://127.0.0.1:{tab.app.port}/test.txt"
        r = requests.get(url)

        if tab.settings.get("share", "autostop_sharing"):
            self.assertFalse('a href="/test.txt"' in r.text)
            r = requests.get(download_file_url)
            self.assertEqual(r.status_code, 404)
            self.download_share(tab)
        else:
            self.assertTrue('a href="/test.txt"' in r.text)
            r = requests.get(download_file_url)

            tmp_file = tempfile.NamedTemporaryFile("wb", delete=False)
            tmp_file.write(r.content)
            tmp_file.close()

            with open(tmp_file.name, "r") as f:
                self.assertEqual("onionshare", f.read())
            os.remove(tmp_file.name)

        QtTest.QTest.qWait(500, self.gui.qtapp)

    def set_autostart_timer(self, tab, timer):
        """Test that the timer can be set"""
        schedule = QtCore.QDateTime.currentDateTime().addSecs(timer)
        tab.get_mode().mode_settings_widget.autostart_timer_widget.setDateTime(schedule)
        self.assertTrue(
            tab.get_mode().mode_settings_widget.autostart_timer_widget.dateTime(),
            schedule,
        )

    def autostart_timer_widget_hidden(self, tab):
        """Test that the auto-start timer widget is hidden when share has started"""
        self.assertFalse(
            tab.get_mode().mode_settings_widget.autostart_timer_widget.isVisible()
        )

    def scheduled_service_started(self, tab, wait):
        """Test that the server has timed out after the timer ran out"""
        QtTest.QTest.qWait(wait, self.gui.qtapp)
        # We should have started now
        self.assertEqual(tab.get_mode().server_status.status, 2)

    def cancel_the_share(self, tab):
        """Test that we can cancel a share before it's started up """
        self.server_working_on_start_button_pressed(tab)
        self.server_status_indicator_says_scheduled(tab)
        self.add_remove_buttons_hidden(tab)
        self.mode_settings_widget_is_hidden(tab)
        self.set_autostart_timer(tab, 10)
        QtTest.QTest.qWait(500, self.gui.qtapp)
        QtTest.QTest.mousePress(
            tab.get_mode().server_status.server_button, QtCore.Qt.LeftButton
        )
        QtTest.QTest.qWait(100, self.gui.qtapp)
        QtTest.QTest.mouseRelease(
            tab.get_mode().server_status.server_button, QtCore.Qt.LeftButton
        )
        QtTest.QTest.qWait(500, self.gui.qtapp)
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_STOPPED,
        )
        self.server_is_stopped(tab)
        self.web_server_is_stopped(tab)

    # Grouped tests follow from here

    def run_all_share_mode_setup_tests(self, tab):
        """Tests in share mode prior to starting a share"""
        tab.get_mode().server_status.file_selection.file_list.add_file(
            self.tmpfile_test
        )
        tab.get_mode().server_status.file_selection.file_list.add_file(self.tmpfiles[0])
        tab.get_mode().server_status.file_selection.file_list.add_file(self.tmpfiles[1])
        self.file_selection_widget_has_files(tab, 3)
        self.history_is_not_visible(tab)
        self.click_toggle_history(tab)
        self.history_is_visible(tab)
        self.removing_all_files_hides_remove_button(tab)
        self.add_a_file_and_remove_using_its_remove_widget(tab)
        self.file_selection_widget_read_files(tab)

    def run_all_share_mode_started_tests(self, tab, startup_time=2000):
        """Tests in share mode after starting a share"""
        self.server_working_on_start_button_pressed(tab)
        self.server_status_indicator_says_starting(tab)
        self.add_remove_buttons_hidden(tab)
        self.mode_settings_widget_is_hidden(tab)
        self.server_is_started(tab, startup_time)
        self.web_server_is_running(tab)
        self.url_description_shown(tab)
        self.url_instructions_shown(tab)
        self.url_shown(tab)
        self.have_copy_url_button(tab)
        self.have_show_url_qr_code_button(tab)
        self.private_key_shown(tab)
        self.client_auth_instructions_shown(tab)
        self.have_show_client_auth_qr_code_button(tab)
        self.server_status_indicator_says_started(tab)

    def run_all_share_mode_download_tests(self, tab):
        """Tests in share mode after downloading a share"""
        tab.get_mode().server_status.file_selection.file_list.add_file(
            self.tmpfile_test
        )
        self.web_page(tab, "Total size")
        self.javascript_is_correct_mime_type(tab, "send.js")
        self.download_share(tab)
        self.history_widgets_present(tab)
        self.server_is_stopped(tab)
        self.web_server_is_stopped(tab)
        self.server_status_indicator_says_closed(tab)
        self.add_button_visible(tab)
        self.server_working_on_start_button_pressed(tab)
        self.toggle_indicator_is_reset(tab)
        self.server_is_started(tab)
        self.history_indicator(tab)

    def run_all_share_mode_individual_file_download_tests(self, tab):
        """Tests in share mode after downloading a share"""
        self.web_page(tab, "Total size")
        self.individual_file_is_viewable_or_not(tab)
        self.history_widgets_present(tab)
        self.server_is_stopped(tab)
        self.web_server_is_stopped(tab)
        self.server_status_indicator_says_closed(tab)
        self.add_button_visible(tab)
        self.server_working_on_start_button_pressed(tab)
        self.server_is_started(tab)
        self.history_indicator(tab)

    def run_all_share_mode_tests(self, tab):
        """End-to-end share tests"""
        self.run_all_share_mode_setup_tests(tab)
        self.run_all_share_mode_started_tests(tab)
        self.run_all_share_mode_download_tests(tab)

    def run_all_clear_all_history_button_tests(self, tab):
        """Test the Clear All history button"""
        self.run_all_share_mode_setup_tests(tab)
        self.run_all_share_mode_started_tests(tab)
        self.individual_file_is_viewable_or_not(tab)
        self.history_widgets_present(tab)
        self.clear_all_history_items(tab, 0)
        self.individual_file_is_viewable_or_not(tab)
        self.clear_all_history_items(tab, 2)

    def run_all_remove_all_file_selection_button_tests(self, tab):
        """Test the Remove All File Selection button"""
        self.run_all_share_mode_setup_tests(tab)
        self.add_a_file_and_remove_using_remove_all_widget(tab)

    def run_all_share_mode_individual_file_tests(self, tab):
        """Tests in share mode when viewing an individual file"""
        self.run_all_share_mode_setup_tests(tab)
        self.run_all_share_mode_started_tests(tab)
        self.run_all_share_mode_individual_file_download_tests(tab)

    # Tests

    def test_autostart_and_autostop_timer_mismatch(self):
        """
        If autostart timer is after autostop timer, a warning should be thrown
        """
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.toggle_advanced_button.click()
        tab.get_mode().mode_settings_widget.autostart_timer_checkbox.click()
        tab.get_mode().mode_settings_widget.autostop_timer_checkbox.click()

        def accept_dialog():
            window = tab.common.gui.qtapp.activeWindow()
            if window:
                window.close()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        self.set_autostart_timer(tab, 15)
        self.set_timeout(tab, 5)
        QtCore.QTimer.singleShot(200, accept_dialog)
        tab.get_mode().server_status.server_button.click()
        self.server_is_stopped(tab)

        self.close_all_tabs()

    def test_autostart_timer(self):
        """
        Autostart timer should automatically start
        """
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.toggle_advanced_button.click()
        tab.get_mode().mode_settings_widget.autostart_timer_checkbox.click()

        self.run_all_common_setup_tests()

        self.run_all_share_mode_setup_tests(tab)
        self.set_autostart_timer(tab, 2)
        self.server_working_on_start_button_pressed(tab)
        self.autostart_timer_widget_hidden(tab)
        self.server_status_indicator_says_scheduled(tab)
        self.web_server_is_stopped(tab)
        self.scheduled_service_started(tab, 2200)
        self.web_server_is_running(tab)

        self.close_all_tabs()

    def test_autostart_timer_too_short(self):
        """
        Autostart timer should throw a warning if the scheduled time is too soon
        """
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.toggle_advanced_button.click()
        tab.get_mode().mode_settings_widget.autostart_timer_checkbox.click()

        def accept_dialog():
            window = tab.common.gui.qtapp.activeWindow()
            if window:
                window.close()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        # Set a low timeout
        self.set_autostart_timer(tab, 2)
        QtTest.QTest.qWait(2200, self.gui.qtapp)
        QtCore.QTimer.singleShot(200, accept_dialog)
        tab.get_mode().server_status.server_button.click()
        self.assertEqual(tab.get_mode().server_status.status, 0)

        self.close_all_tabs()

    def test_autostart_timer_cancel(self):
        """
        Test canceling a scheduled share
        """
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.toggle_advanced_button.click()
        tab.get_mode().mode_settings_widget.autostart_timer_checkbox.click()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        self.cancel_the_share(tab)

        self.close_all_tabs()

    def test_clear_all_history_button(self):
        """
        Test clearing all history items
        """
        tab = self.new_share_tab()
        tab.get_mode().autostop_sharing_checkbox.click()

        self.run_all_common_setup_tests()
        self.run_all_clear_all_history_button_tests(tab)

        self.close_all_tabs()

    def test_remove_all_file_selection_button(self):
        """
        Test remove all file items at once
        """
        tab = self.new_share_tab()

        self.run_all_common_setup_tests()
        self.run_all_remove_all_file_selection_button_tests(tab)

        self.close_all_tabs()

    def test_public_mode(self):
        """
        Public mode shouldn't have a password
        """
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.public_checkbox.click()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_tests(tab)

        self.close_all_tabs()

    def test_without_autostop_sharing(self):
        """
        Disable autostop sharing after first download
        """
        tab = self.new_share_tab()
        tab.get_mode().autostop_sharing_checkbox.click()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_tests(tab)

        self.close_all_tabs()

    def test_download(self):
        """
        Test downloading in share mode
        """
        tab = self.new_share_tab()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_tests(tab)

        self.close_all_tabs()

    def test_individual_files_without_autostop_sharing(self):
        """
        Test downloading individual files with autostop sharing disabled
        """
        tab = self.new_share_tab()
        tab.get_mode().autostop_sharing_checkbox.click()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_individual_file_tests(tab)

        self.close_all_tabs()

    def test_individual_files(self):
        """
        Test downloading individual files
        """
        tab = self.new_share_tab()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_individual_file_tests(tab)

        self.close_all_tabs()

    def test_large_download(self):
        """
        Test a large download
        """
        tab = self.new_share_tab()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        tab.get_mode().server_status.file_selection.file_list.add_file(
            self.tmpfile_large
        )
        self.run_all_share_mode_started_tests(tab, startup_time=15000)
        self.assertTrue(tab.get_mode().filesize_warning.isVisible())
        self.download_share(tab)
        self.server_is_stopped(tab)
        self.web_server_is_stopped(tab)
        self.server_status_indicator_says_closed(tab)

        self.close_all_tabs()

    def test_autostop_timer(self):
        """
        Test the autostop timer
        """
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.toggle_advanced_button.click()
        tab.get_mode().mode_settings_widget.autostop_timer_checkbox.click()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        self.set_timeout(tab, 5)
        self.run_all_share_mode_started_tests(tab)
        self.autostop_timer_widget_hidden(tab)
        self.server_timed_out(tab, 10000)
        self.web_server_is_stopped(tab)

        self.close_all_tabs()

    def test_autostop_timer_too_short(self):
        """
        Test the autostop timer when the timeout is too short
        """
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.toggle_advanced_button.click()
        tab.get_mode().mode_settings_widget.autostop_timer_checkbox.click()

        def accept_dialog():
            window = tab.common.gui.qtapp.activeWindow()
            if window:
                window.close()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        # Set a low timeout
        self.set_timeout(tab, 2)
        QtTest.QTest.qWait(2100, self.gui.qtapp)
        QtCore.QTimer.singleShot(2200, accept_dialog)
        tab.get_mode().server_status.server_button.click()
        self.assertEqual(tab.get_mode().server_status.status, 0)

        self.close_all_tabs()

    def test_unreadable_file(self):
        """
        Sharing an unreadable file should throw a warning
        """
        tab = self.new_share_tab()

        def accept_dialog():
            window = tab.common.gui.qtapp.activeWindow()
            if window:
                window.close()

        self.run_all_share_mode_setup_tests(tab)
        QtCore.QTimer.singleShot(200, accept_dialog)
        tab.get_mode().server_status.file_selection.file_list.add_file(
            "/tmp/nonexistent.txt"
        )
        self.file_selection_widget_has_files(tab, 3)

        self.close_all_tabs()

    def test_client_auth(self):
        """
        Test the ClientAuth is received from the backend,
        that the widget is visible in the UI and that the
        clipboard contains the ClientAuth string
        """
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.toggle_advanced_button.click()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        self.run_all_share_mode_started_tests(tab)
        self.clientauth_is_visible(tab)

        self.close_all_tabs()

        # Now try in public mode
        tab = self.new_share_tab()
        tab.get_mode().mode_settings_widget.public_checkbox.click()
        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        self.run_all_share_mode_started_tests(tab)
        self.clientauth_is_not_visible(tab)

        self.close_all_tabs()


    def test_405_page_returned_for_invalid_methods(self):
        """
        Our custom 405 page should return for invalid methods
        """
        tab = self.new_share_tab()

        tab.get_mode().autostop_sharing_checkbox.click()
        tab.get_mode().mode_settings_widget.public_checkbox.click()

        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests(tab)
        self.run_all_share_mode_started_tests(tab)

        url = f"http://127.0.0.1:{tab.app.port}/"
        self.hit_405(url, expected_resp="OnionShare: 405 Method Not Allowed", data = {'foo':'bar'}, methods = ["put", "post", "delete", "options"])
        self.history_widgets_present(tab)
        self.close_all_tabs()
