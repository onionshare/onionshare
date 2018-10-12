import os
import requests
from PyQt5 import QtTest
from .TorGuiBaseTest import TorGuiBaseTest

class TorGuiReceiveTest(TorGuiBaseTest):

    def upload_file(self, public_mode, expected_file):
        '''Test that we can upload the file'''
        (socks_address, socks_port) = self.gui.app.onion.get_tor_socks_port()
        session = requests.session()
        session.proxies = {}
        session.proxies['http'] = 'socks5h://{}:{}'.format(socks_address, socks_port)
        files = {'file[]': open('/tmp/test.txt', 'rb')}
        if not public_mode:
            path = 'http://{}/{}/upload'.format(self.gui.app.onion_host, self.gui.receive_mode.web.slug)
        else:
            path = 'http://{}/upload'.format(self.gui.app.onion_host)
        response = session.post(path, files=files)
        QtTest.QTest.qWait(4000)
        self.assertTrue(os.path.isfile(expected_file))

    def run_all_receive_mode_tests(self, public_mode, receive_allow_receiver_shutdown):
        self.click_mode(self.gui.receive_mode)
        self.history_is_not_visible(self.gui.receive_mode)
        self.click_toggle_history(self.gui.receive_mode)
        self.history_is_visible(self.gui.receive_mode)
        self.server_working_on_start_button_pressed(self.gui.receive_mode)
        self.server_status_indicator_says_starting(self.gui.receive_mode)
        self.settings_button_is_hidden()
        self.a_server_is_started(self.gui.receive_mode)
        self.a_web_server_is_running()
        self.have_an_onion_service()
        self.have_a_slug(self.gui.receive_mode, public_mode)
        self.url_description_shown(self.gui.receive_mode)
        self.have_copy_url_button(self.gui.receive_mode)
        self.server_status_indicator_says_started(self.gui.receive_mode)
        self.web_page(self.gui.receive_mode, 'Select the files you want to send, then click', public_mode)
        self.upload_file(public_mode, '/tmp/OnionShare/test.txt')
        self.history_widgets_present(self.gui.receive_mode)
        self.counter_incremented(self.gui.receive_mode, 1)
        self.upload_file(public_mode, '/tmp/OnionShare/test-2.txt')
        self.counter_incremented(self.gui.receive_mode, 2)
        self.history_indicator(self.gui.receive_mode, public_mode)
        self.server_is_stopped(self.gui.receive_mode, False)
        self.web_service_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)
        self.server_working_on_start_button_pressed(self.gui.receive_mode)
        self.a_server_is_started(self.gui.receive_mode)
        self.history_indicator(self.gui.receive_mode, public_mode)

