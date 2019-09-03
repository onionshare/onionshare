import os
import requests
from datetime import datetime, timedelta
from PyQt5 import QtCore, QtTest
from onionshare import strings
from .GuiBaseTest import GuiBaseTest

class GuiReceiveTest(GuiBaseTest):
    def upload_file(self, public_mode, file_to_upload, expected_basename, identical_files_at_once=False):
        '''Test that we can upload the file'''

        # Wait 2 seconds to make sure the filename, based on timestamp, isn't accidentally reused
        QtTest.QTest.qWait(2000)

        files = {'file[]': open(file_to_upload, 'rb')}
        url = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)
        if public_mode:
            r = requests.post(url, files=files)
            if identical_files_at_once:
                # Send a duplicate upload to test for collisions
                r = requests.post(url, files=files)
        else:
            r = requests.post(url, files=files, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.receive_mode.web.password))
            if identical_files_at_once:
                # Send a duplicate upload to test for collisions
                r = requests.post(url, files=files, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.receive_mode.web.password))

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
            receive_mode_dir = os.path.join(self.gui.common.settings.get('data_dir'), date_dir, time_dir)
            expected_filename = os.path.join(receive_mode_dir, expected_basename)
            if os.path.exists(expected_filename):
                exists = True
                break
            now = now - timedelta(seconds=1)

        self.assertTrue(exists)

    def upload_file_should_fail(self, public_mode):
        '''Test that we can't upload the file when permissions are wrong, and expected content is shown'''
        files = {'file[]': open('/tmp/test.txt', 'rb')}
        url = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)
        if public_mode:
            r = requests.post(url, files=files)
        else:
            r = requests.post(url, files=files, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.receive_mode.web.password))

        QtCore.QTimer.singleShot(1000, self.accept_dialog)
        self.assertTrue('Error uploading, please inform the OnionShare user' in r.text)

    def upload_too_large_file(self, mode, public_mode):
        '''Test that we can't upload a file that is too large'''
        size = 2097152
        with open('/tmp/large_file', 'wb') as fout:
            fout.write(os.urandom(size))
        files = {'file[]': open('/tmp/large_file', 'rb')}
        url = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)
        if public_mode:
            r = requests.post(url, files=files)
        else:
            r = requests.post(url, files=files, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.receive_mode.web.password))

        QtCore.QTimer.singleShot(1000, self.accept_dialog)
        self.assertEqual(r.status_code, 500)
        QtTest.QTest.qWait(1000)
        self.assertTrue(mode.status_bar.currentMessage(), strings._('receive_mode_upload_too_large'))
        self.assertTrue(mode.history.empty.isVisible())
        self.assertFalse(mode.history.not_empty.isVisible())

    def upload_dir_permissions(self, mode=0o755):
        '''Manipulate the permissions on the upload dir in between tests'''
        os.chmod('/tmp/OnionShare', mode)

    def try_without_auth_in_non_public_mode(self):
        r = requests.post('http://127.0.0.1:{}/upload'.format(self.gui.app.port))
        self.assertEqual(r.status_code, 401)
        r = requests.get('http://127.0.0.1:{}/close'.format(self.gui.app.port))
        self.assertEqual(r.status_code, 401)

    def uploading_zero_files_shouldnt_change_ui(self, mode, public_mode):
        '''If you submit the receive mode form without selecting any files, the UI shouldn't get updated'''
        url = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)

        # What were the counts before submitting the form?
        before_in_progress_count = mode.history.in_progress_count
        before_completed_count = mode.history.completed_count
        before_number_of_history_items = len(mode.history.item_list.items)

        # Click submit without including any files a few times
        if public_mode:
            r = requests.post(url, files={})
            r = requests.post(url, files={})
            r = requests.post(url, files={})
        else:
            auth = requests.auth.HTTPBasicAuth('onionshare', mode.web.password)
            r = requests.post(url, files={}, auth=auth)
            r = requests.post(url, files={}, auth=auth)
            r = requests.post(url, files={}, auth=auth)

        # The counts shouldn't change
        self.assertEqual(mode.history.in_progress_count, before_in_progress_count)
        self.assertEqual(mode.history.completed_count, before_completed_count)
        self.assertEqual(len(mode.history.item_list.items), before_number_of_history_items)

    # 'Grouped' tests follow from here

    def run_all_receive_mode_setup_tests(self, public_mode):
        '''Set up a share in Receive mode and start it'''
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
        self.web_page(self.gui.receive_mode, 'Select the files you want to send, then click', public_mode)

    def run_all_receive_mode_tests(self, public_mode):
        '''Upload files in receive mode and stop the share'''
        self.run_all_receive_mode_setup_tests(public_mode)
        if not public_mode:
            self.try_without_auth_in_non_public_mode()
        self.upload_file(public_mode, '/tmp/test.txt', 'test.txt')
        self.history_widgets_present(self.gui.receive_mode)
        self.counter_incremented(self.gui.receive_mode, 1)
        self.upload_file(public_mode, '/tmp/test.txt', 'test.txt')
        self.counter_incremented(self.gui.receive_mode, 2)
        self.upload_file(public_mode, '/tmp/testdir/test', 'test')
        self.counter_incremented(self.gui.receive_mode, 3)
        self.upload_file(public_mode, '/tmp/testdir/test', 'test')
        self.counter_incremented(self.gui.receive_mode, 4)
        # Test uploading the same file twice at the same time, and make sure no collisions
        self.upload_file(public_mode, '/tmp/test.txt', 'test.txt', True)
        self.counter_incremented(self.gui.receive_mode, 6)
        self.uploading_zero_files_shouldnt_change_ui(self.gui.receive_mode, public_mode)
        self.history_indicator(self.gui.receive_mode, public_mode)
        self.server_is_stopped(self.gui.receive_mode, False)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)
        self.server_working_on_start_button_pressed(self.gui.receive_mode)
        self.server_is_started(self.gui.receive_mode)
        self.history_indicator(self.gui.receive_mode, public_mode)

    def run_all_receive_mode_unwritable_dir_tests(self, public_mode):
        '''Attempt to upload (unwritable) files in receive mode and stop the share'''
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

    def receive_mode_upload_too_large_test(self, public_mode):
        self.run_all_receive_mode_setup_tests(public_mode)
        self.upload_too_large_file(self.gui.receive_mode, public_mode)
        self.server_is_stopped(self.gui.receive_mode, False)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)
