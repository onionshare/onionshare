import os
import requests
from PyQt5 import QtCore, QtTest
from .GuiBaseTest import GuiBaseTest

class GuiReceiveTest(GuiBaseTest):
    def upload_file(self, public_mode, expected_file):
        '''Test that we can upload the file'''
        files = {'file[]': open('/tmp/test.txt', 'rb')}
        if not public_mode:
            path = 'http://127.0.0.1:{}/{}/upload'.format(self.gui.app.port, self.gui.receive_mode.web.slug)
        else:
            path = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)
        response = requests.post(path, files=files)
        QtTest.QTest.qWait(2000)
        self.assertTrue(os.path.isfile(expected_file))

    def upload_file_should_fail(self, public_mode, expected_file):
        '''Test that we can't upload the file when permissions are wrong, and expected content is shown'''
        files = {'file[]': open('/tmp/test.txt', 'rb')}
        if not public_mode:
            path = 'http://127.0.0.1:{}/{}/upload'.format(self.gui.app.port, self.gui.receive_mode.web.slug)
        else:
            path = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)
        response = requests.post(path, files=files)

        QtCore.QTimer.singleShot(1000, self.accept_dialog)
        self.assertTrue('Error uploading, please inform the OnionShare user' in response.text)

    def upload_dir_permissions(self, mode=0o755):
        '''Manipulate the permissions on the upload dir in between tests'''
        os.chmod('/tmp/OnionShare', mode)

    def run_receive_mode_sender_closed_tests(self, public_mode):
        '''Test that the share can be stopped by the sender in receive mode'''
        if not public_mode:
            path = 'http://127.0.0.1:{}/{}/close'.format(self.gui.app.port, self.gui.receive_mode.web.slug)
        else:
            path = 'http://127.0.0.1:{}/close'.format(self.gui.app.port)
        response = requests.post(path)
        self.server_is_stopped(self.gui.receive_mode, False)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)


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
        self.have_a_slug(self.gui.receive_mode, public_mode)
        self.url_description_shown(self.gui.receive_mode)
        self.have_copy_url_button(self.gui.receive_mode, public_mode)
        self.server_status_indicator_says_started(self.gui.receive_mode)
        self.web_page(self.gui.receive_mode, 'Select the files you want to send, then click', public_mode)

    def run_all_receive_mode_tests(self, public_mode, receive_allow_receiver_shutdown):
        '''Upload files in receive mode and stop the share'''
        self.run_all_receive_mode_setup_tests(public_mode)
        self.upload_file(public_mode, '/tmp/OnionShare/test.txt')
        self.history_widgets_present(self.gui.receive_mode)
        self.counter_incremented(self.gui.receive_mode, 1)
        self.upload_file(public_mode, '/tmp/OnionShare/test-2.txt')
        self.counter_incremented(self.gui.receive_mode, 2)
        self.history_indicator(self.gui.receive_mode, public_mode)
        self.server_is_stopped(self.gui.receive_mode, False)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)
        self.server_working_on_start_button_pressed(self.gui.receive_mode)
        self.server_is_started(self.gui.receive_mode)
        self.history_indicator(self.gui.receive_mode, public_mode)

    def run_all_receive_mode_unwritable_dir_tests(self, public_mode, receive_allow_receiver_shutdown):
        '''Attempt to upload (unwritable) files in receive mode and stop the share'''
        self.run_all_receive_mode_setup_tests(public_mode)
        self.upload_dir_permissions(0o400)
        self.upload_file_should_fail(public_mode, '/tmp/OnionShare/test.txt')
        self.server_is_stopped(self.gui.receive_mode, True)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)
        self.upload_dir_permissions(0o755)

    def run_all_receive_mode_timer_tests(self, public_mode):
        """Auto-stop timer tests in receive mode"""
        self.run_all_receive_mode_setup_tests(public_mode)
        self.set_timeout(self.gui.receive_mode, 5)
        self.timeout_widget_hidden(self.gui.receive_mode)
        self.server_timed_out(self.gui.receive_mode, 15000)
        self.web_server_is_stopped()
