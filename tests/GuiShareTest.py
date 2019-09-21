import os
import requests
import socks
import zipfile
import tempfile
from PyQt5 import QtCore, QtTest
from .GuiBaseTest import GuiBaseTest

class GuiShareTest(GuiBaseTest):
    # Persistence tests
    def have_same_password(self, password):
        '''Test that we have the same password'''
        self.assertEqual(self.gui.share_mode.server_status.web.password, password)

    # Share-specific tests

    def file_selection_widget_has_files(self, num=2):
        '''Test that the number of items in the list is as expected'''
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), num)


    def deleting_all_files_hides_delete_button(self):
        '''Test that clicking on the file item shows the delete button. Test that deleting the only item in the list hides the delete button'''
        rect = self.gui.share_mode.server_status.file_selection.file_list.visualItemRect(self.gui.share_mode.server_status.file_selection.file_list.item(0))
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.viewport(), QtCore.Qt.LeftButton, pos=rect.center())
        # Delete button should be visible
        self.assertTrue(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())
        # Click delete, delete button should still be visible since we have one more file
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.delete_button, QtCore.Qt.LeftButton)

        rect = self.gui.share_mode.server_status.file_selection.file_list.visualItemRect(self.gui.share_mode.server_status.file_selection.file_list.item(0))
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.viewport(), QtCore.Qt.LeftButton, pos=rect.center())
        self.assertTrue(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.delete_button, QtCore.Qt.LeftButton)

        # No more files, the delete button should be hidden
        self.assertFalse(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())


    def add_a_file_and_delete_using_its_delete_widget(self):
        '''Test that we can also delete a file by clicking on its [X] widget'''
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/etc/hosts')
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.item(0).item_button, QtCore.Qt.LeftButton)
        self.file_selection_widget_has_files(0)


    def file_selection_widget_read_files(self):
        '''Re-add some files to the list so we can share'''
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/etc/hosts')
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/tmp/test.txt')
        self.file_selection_widget_has_files(2)


    def add_large_file(self):
        '''Add a large file to the share'''
        size = 1024*1024*155
        with open('/tmp/large_file', 'wb') as fout:
            fout.write(os.urandom(size))
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/tmp/large_file')


    def add_delete_buttons_hidden(self):
        '''Test that the add and delete buttons are hidden when the server starts'''
        self.assertFalse(self.gui.share_mode.server_status.file_selection.add_button.isVisible())
        self.assertFalse(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())


    def download_share(self, public_mode):
        '''Test that we can download the share'''
        url = "http://127.0.0.1:{}/download".format(self.gui.app.port)
        if public_mode:
            r = requests.get(url)
        else:
            r = requests.get(url, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.share_mode.server_status.web.password))

        tmp_file = tempfile.NamedTemporaryFile()
        with open(tmp_file.name, 'wb') as f:
            f.write(r.content)

        zip = zipfile.ZipFile(tmp_file.name)
        QtTest.QTest.qWait(2000)
        self.assertEqual('onionshare', zip.read('test.txt').decode('utf-8'))

    def individual_file_is_viewable_or_not(self, public_mode, stay_open):
        '''Test whether an individual file is viewable (when in stay_open mode) and that it isn't (when not in stay_open mode)'''
        url = "http://127.0.0.1:{}".format(self.gui.app.port)
        download_file_url = "http://127.0.0.1:{}/test.txt".format(self.gui.app.port)
        if public_mode:
            r = requests.get(url)
        else:
            r = requests.get(url, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.share_mode.server_status.web.password))

        if stay_open:
            self.assertTrue('a href="test.txt"' in r.text)

            if public_mode:
                r = requests.get(download_file_url)
            else:
                r = requests.get(download_file_url, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.share_mode.server_status.web.password))

            tmp_file = tempfile.NamedTemporaryFile()
            with open(tmp_file.name, 'wb') as f:
                f.write(r.content)

            with open(tmp_file.name, 'r') as f:
                self.assertEqual('onionshare', f.read())
        else:
            self.assertFalse('a href="/test.txt"' in r.text)
            if public_mode:
                r = requests.get(download_file_url)
            else:
                r = requests.get(download_file_url, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.share_mode.server_status.web.password))
            self.assertEqual(r.status_code, 404)
            self.download_share(public_mode)

        QtTest.QTest.qWait(2000)

    def hit_401(self, public_mode):
        '''Test that the server stops after too many 401s, or doesn't when in public_mode'''
        url = "http://127.0.0.1:{}/".format(self.gui.app.port)

        for _ in range(20):
            password_guess = self.gui.common.build_password()
            r = requests.get(url, auth=requests.auth.HTTPBasicAuth('onionshare', password_guess))

        # A nasty hack to avoid the Alert dialog that blocks the rest of the test
        if not public_mode:
            QtCore.QTimer.singleShot(1000, self.accept_dialog)

        # In public mode, we should still be running (no rate-limiting)
        if public_mode:
            self.web_server_is_running()
        # In non-public mode, we should be shut down (rate-limiting)
        else:
            self.web_server_is_stopped()


    # 'Grouped' tests follow from here

    def run_all_share_mode_setup_tests(self):
        """Tests in share mode prior to starting a share"""
        self.click_mode(self.gui.share_mode)
        self.file_selection_widget_has_files()
        self.history_is_not_visible(self.gui.share_mode)
        self.click_toggle_history(self.gui.share_mode)
        self.history_is_visible(self.gui.share_mode)
        self.deleting_all_files_hides_delete_button()
        self.add_a_file_and_delete_using_its_delete_widget()
        self.file_selection_widget_read_files()


    def run_all_share_mode_started_tests(self, public_mode, startup_time=2000):
        """Tests in share mode after starting a share"""
        self.server_working_on_start_button_pressed(self.gui.share_mode)
        self.server_status_indicator_says_starting(self.gui.share_mode)
        self.add_delete_buttons_hidden()
        self.settings_button_is_hidden()
        self.server_is_started(self.gui.share_mode, startup_time)
        self.web_server_is_running()
        self.have_a_password(self.gui.share_mode, public_mode)
        self.url_description_shown(self.gui.share_mode)
        self.have_copy_url_button(self.gui.share_mode, public_mode)
        self.server_status_indicator_says_started(self.gui.share_mode)


    def run_all_share_mode_download_tests(self, public_mode, stay_open):
        """Tests in share mode after downloading a share"""
        self.web_page(self.gui.share_mode, 'Total size', public_mode)
        self.download_share(public_mode)
        self.history_widgets_present(self.gui.share_mode)
        self.server_is_stopped(self.gui.share_mode, stay_open)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.share_mode, stay_open)
        self.add_button_visible(self.gui.share_mode)
        self.server_working_on_start_button_pressed(self.gui.share_mode)
        self.toggle_indicator_is_reset(self.gui.share_mode)
        self.server_is_started(self.gui.share_mode)
        self.history_indicator(self.gui.share_mode, public_mode)

    def run_all_share_mode_individual_file_download_tests(self, public_mode, stay_open):
        """Tests in share mode after downloading a share"""
        self.web_page(self.gui.share_mode, 'Total size', public_mode)
        self.individual_file_is_viewable_or_not(public_mode, stay_open)
        self.history_widgets_present(self.gui.share_mode)
        self.server_is_stopped(self.gui.share_mode, stay_open)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.share_mode, stay_open)
        self.add_button_visible(self.gui.share_mode)
        self.server_working_on_start_button_pressed(self.gui.share_mode)
        self.server_is_started(self.gui.share_mode)
        self.history_indicator(self.gui.share_mode, public_mode)

    def run_all_share_mode_tests(self, public_mode, stay_open):
        """End-to-end share tests"""
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(public_mode)
        self.run_all_share_mode_download_tests(public_mode, stay_open)

    def run_all_clear_all_button_tests(self, public_mode, stay_open):
        """Test the Clear All history button"""
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(public_mode)
        self.individual_file_is_viewable_or_not(public_mode, stay_open)
        self.history_widgets_present(self.gui.share_mode)
        self.clear_all_history_items(self.gui.share_mode, 0)
        self.individual_file_is_viewable_or_not(public_mode, stay_open)
        self.clear_all_history_items(self.gui.share_mode, 2)

    def run_all_share_mode_individual_file_tests(self, public_mode, stay_open):
        """Tests in share mode when viewing an individual file"""
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(public_mode)
        self.run_all_share_mode_individual_file_download_tests(public_mode, stay_open)

    def run_all_large_file_tests(self, public_mode, stay_open):
        """Same as above but with a larger file"""
        self.run_all_share_mode_setup_tests()
        self.add_large_file()
        self.run_all_share_mode_started_tests(public_mode, startup_time=15000)
        self.assertTrue(self.gui.share_mode.filesize_warning.isVisible())
        self.server_is_stopped(self.gui.share_mode, stay_open)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.share_mode, stay_open)


    def run_all_share_mode_persistent_tests(self, public_mode, stay_open):
        """Same as end-to-end share tests but also test the password is the same on multiple shared"""
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(public_mode)
        password = self.gui.share_mode.server_status.web.password
        self.run_all_share_mode_download_tests(public_mode, stay_open)
        self.have_same_password(password)


    def run_all_share_mode_timer_tests(self, public_mode):
        """Auto-stop timer tests in share mode"""
        self.run_all_share_mode_setup_tests()
        self.set_timeout(self.gui.share_mode, 5)
        self.run_all_share_mode_started_tests(public_mode)
        self.autostop_timer_widget_hidden(self.gui.share_mode)
        self.server_timed_out(self.gui.share_mode, 10000)
        self.web_server_is_stopped()

    def run_all_share_mode_autostart_timer_tests(self, public_mode):
        """Auto-start timer tests in share mode"""
        self.run_all_share_mode_setup_tests()
        self.set_autostart_timer(self.gui.share_mode, 5)
        self.server_working_on_start_button_pressed(self.gui.share_mode)
        self.autostart_timer_widget_hidden(self.gui.share_mode)
        self.server_status_indicator_says_scheduled(self.gui.share_mode)
        self.web_server_is_stopped()
        self.scheduled_service_started(self.gui.share_mode, 7000)
        self.web_server_is_running()

    def run_all_share_mode_autostop_autostart_mismatch_tests(self, public_mode):
        """Auto-stop timer tests in share mode"""
        self.run_all_share_mode_setup_tests()
        self.set_autostart_timer(self.gui.share_mode, 15)
        self.set_timeout(self.gui.share_mode, 5)
        QtCore.QTimer.singleShot(4000, self.accept_dialog)
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.server_is_stopped(self.gui.share_mode, False)

    def run_all_share_mode_unreadable_file_tests(self):
        '''Attempt to share an unreadable file'''
        self.run_all_share_mode_setup_tests()
        QtCore.QTimer.singleShot(1000, self.accept_dialog)
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/tmp/nonexistent.txt')
        self.file_selection_widget_has_files(2)
