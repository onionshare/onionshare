import os
import requests
from PyQt5 import QtTest
from .TorGuiBaseTest import TorGuiBaseTest


class TorGuiReceiveTest(TorGuiBaseTest):
    def upload_file(self, public_mode, file_to_upload, expected_file):
        """Test that we can upload the file"""
        (socks_address, socks_port) = self.gui.app.onion.get_tor_socks_port()
        session = requests.session()
        session.proxies = {}
        session.proxies["http"] = f"socks5h://{socks_address}:{socks_port}"
        files = {"file[]": open(file_to_upload, "rb")}
        if not public_mode:
            path = f"http://{self.gui.app.onion_host}/{self.gui.receive_mode.web.password}/upload"
        else:
            path = f"http://{self.gui.app.onion_host}/upload"
        response = session.post(path, files=files)
        QtTest.QTest.qWait(4000)
        self.assertTrue(os.path.isfile(expected_file))

    # 'Grouped' tests follow from here

    def run_all_receive_mode_tests(self, public_mode, receive_allow_receiver_shutdown):
        """Run a full suite of tests in Receive mode"""
        self.click_mode(self.gui.receive_mode)
        self.history_is_not_visible(self.gui.receive_mode)
        self.click_toggle_history(self.gui.receive_mode)
        self.history_is_visible(self.gui.receive_mode)
        self.server_working_on_start_button_pressed(self.gui.receive_mode)
        self.server_status_indicator_says_starting(self.gui.receive_mode)
        self.settings_button_is_hidden()
        self.server_is_started(self.gui.receive_mode, startup_time=45000)
        self.web_server_is_running()
        self.have_an_onion_service()
        self.have_a_password(self.gui.receive_mode, public_mode)
        self.url_description_shown(self.gui.receive_mode)
        self.have_copy_url_button(self.gui.receive_mode, public_mode)
        self.server_status_indicator_says_started(self.gui.receive_mode)
        self.web_page(
            self.gui.receive_mode,
            "Select the files you want to send, then click",
            public_mode,
        )
        self.upload_file(public_mode, "/tmp/test.txt", "/tmp/OnionShare/test.txt")
        self.history_widgets_present(self.gui.receive_mode)
        self.counter_incremented(self.gui.receive_mode, 1)
        self.upload_file(public_mode, "/tmp/test.txt", "/tmp/OnionShare/test-2.txt")
        self.counter_incremented(self.gui.receive_mode, 2)
        self.upload_file(public_mode, "/tmp/testdir/test", "/tmp/OnionShare/test")
        self.counter_incremented(self.gui.receive_mode, 3)
        self.upload_file(public_mode, "/tmp/testdir/test", "/tmp/OnionShare/test-2")
        self.counter_incremented(self.gui.receive_mode, 4)
        self.history_indicator(self.gui.receive_mode, public_mode)
        self.server_is_stopped(self.gui.receive_mode, False)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.receive_mode, False)
        self.server_working_on_start_button_pressed(self.gui.receive_mode)
        self.server_is_started(self.gui.receive_mode, startup_time=45000)
        self.history_indicator(self.gui.receive_mode, public_mode)
