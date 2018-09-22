#!/usr/bin/env python3
import os
import sys
import unittest
import socket
import pytest
import zipfile
import socks
import json
import requests

from PyQt5 import QtCore, QtWidgets, QtTest

from onionshare.common import Common
from onionshare.web import Web
from onionshare import onion, strings
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class OnionShareGuiTest(unittest.TestCase):
    '''Test the OnionShare GUI'''
    @classmethod
    def setUpClass(cls):
        '''Create the GUI'''
        # Create our test file
        testfile = open('/tmp/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()
        common = Common()
        common.define_css()

        # Start the Onion
        strings.load_strings(common)

        testonion = onion.Onion(common)
        global qtapp
        qtapp = Application(common)
        app = OnionShare(common, testonion, True, 0)

        web = Web(common, False, True)

        test_settings = {
            "auth_password": "",
            "auth_type": "no_auth",
            "autoupdate_timestamp": "",
            "close_after_first_download": True,
            "connection_type": "bundled",
            "control_port_address": "127.0.0.1",
            "control_port_port": 9051,
            "downloads_dir": "/tmp/OnionShare",
            "hidservauth_string": "",
            "no_bridges": True, 
            "private_key": "",
            "public_mode": True,
            "receive_allow_receiver_shutdown": True,
            "save_private_key": False,
            "shutdown_timeout": False,
            "slug": "",
            "socks_address": "127.0.0.1",
            "socks_port": 9050,
            "socket_file_path": "/var/run/tor/control",
            "systray_notifications": True,
            "tor_bridges_use_meek_lite_azure": False,
            "tor_bridges_use_meek_lite_amazon": False,
            "tor_bridges_use_custom_bridges": "",
            "tor_bridges_use_obfs4": False,
            "use_stealth": False,
            "use_legacy_v2_onions": False,
            "use_autoupdate": True,
            "version": "1.3.1"
        }
        testsettings = '/tmp/testsettings.json'
        open(testsettings, 'w').write(json.dumps(test_settings))

        cls.gui = OnionShareGui(common, testonion, qtapp, app, ['/tmp/test.txt'], testsettings, True)
        
    @classmethod
    def tearDownClass(cls):
        '''Clean up after tests'''
        os.remove('/tmp/test.txt')
        os.remove('/tmp/OnionShare/test.txt')
        os.remove('/tmp/OnionShare/test-2.txt')

    @pytest.mark.run(order=1)
    def test_gui_loaded_and_tor_bootstrapped(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    @pytest.mark.run(order=2)
    def test_windowTitle_seen(self):
        '''Test that the window title is OnionShare'''
        self.assertEqual(self.gui.windowTitle(), 'OnionShare')

    @pytest.mark.run(order=3)
    def test_settings_button_is_visible(self):
        '''Test that the settings button is visible'''
        self.assertTrue(self.gui.settings_button.isVisible())

    @pytest.mark.run(order=4)
    def test_server_status_bar_is_visible(self):
        '''Test that the status bar is visible'''
        self.assertTrue(self.gui.status_bar.isVisible())

    @pytest.mark.run(order=5)
    def test_info_widget_is_not_visible(self):
        '''Test that the info widget along top of screen is not shown because we have a file'''
        self.assertFalse(self.gui.receive_mode.info_widget.isVisible())

    @pytest.mark.run(order=6)
    def test_click_receive_mode(self):
        '''Test that we can switch to Receive Mode by clicking the button'''
        QtTest.QTest.mouseClick(self.gui.receive_mode_button, QtCore.Qt.LeftButton)
        self.assertTrue(self.gui.mode, self.gui.MODE_RECEIVE)

    @pytest.mark.run(order=7)
    def test_uploads_section_is_visible(self):
        '''Test that the Uploads section is visible and that the No Uploads Yet label is present'''
        self.assertTrue(self.gui.receive_mode.uploads.isVisible())
        self.assertTrue(self.gui.receive_mode.uploads.no_uploads_label.isVisible())

    @pytest.mark.run(order=8)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.receive_mode.server_status.server_button, QtCore.Qt.LeftButton)

        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.receive_mode.server_status.status, 1)

    @pytest.mark.run(order=9)
    def test_server_status_indicator_says_starting(self):
        '''Test that the Server Status indicator shows we are Starting'''
        self.assertEquals(self.gui.receive_mode.server_status_label.text(), strings._('gui_status_indicator_share_working', True))

    @pytest.mark.run(order=10)
    def test_settings_button_is_hidden(self):
        '''Test that the settings button is hidden when the server starts'''
        self.assertFalse(self.gui.settings_button.isVisible())

    @pytest.mark.run(order=11)
    def test_a_server_is_started(self):
        '''Test that the server has started'''
        QtTest.QTest.qWait(2000)
        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.receive_mode.server_status.status, 2)

    @pytest.mark.run(order=12)
    def test_a_web_server_is_running(self):
        '''Test that the web server has started'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.assertEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    # Running in local mode, so we have no .onion
    #@pytest.mark.run(order=13)
    #def test_have_an_onion_service(self):
    #    '''Test that we have a valid Onion URL'''
    #    self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')
    #    self.assertEqual(len(self.gui.app.onion_host), 62)

    @pytest.mark.run(order=14)
    def test_have_no_slug(self):
        '''Test that we have a valid slug'''
        self.assertIsNone(self.gui.share_mode.server_status.web.slug)

    @pytest.mark.run(order=15)
    def test_url_description_shown(self):
        '''Test that the URL label is showing'''
        self.assertTrue(self.gui.receive_mode.server_status.url_description.isVisible())

    @pytest.mark.run(order=16)
    def test_have_copy_url_button(self):
        '''Test that the Copy URL button is shown'''
        self.assertTrue(self.gui.receive_mode.server_status.copy_url_button.isVisible())

    @pytest.mark.run(order=17)
    def test_server_status_indicator_says_sharing(self):
        '''Test that the Server Status indicator shows we are Receiving'''
        self.assertEquals(self.gui.receive_mode.server_status_label.text(), strings._('gui_status_indicator_receive_started', True))

    @pytest.mark.run(order=18)
    def test_web_page(self):
        '''Test that the web page contains the term Select the files you want to send, then click'''
        s = socks.socksocket()
        s.settimeout(60)
        s.connect(('127.0.0.1', self.gui.app.port))

        http_request = 'GET / HTTP/1.0\r\n'
        http_request += 'Host: 127.0.0.1\r\n'
        http_request += '\r\n'
        s.sendall(http_request.encode('utf-8'))

        with open('/tmp/webpage', 'wb') as file_to_write:
            while True:
               data = s.recv(1024)
               if not data:
                   break
               file_to_write.write(data)
            file_to_write.close()

        f = open('/tmp/webpage')
        self.assertTrue('Select the files you want to send, then click "Send Files"' in f.read())
        f.close()

    @pytest.mark.run(order=19)
    def test_upload_file(self):
        '''Test that we can upload the file'''
        files = {'file[]': open('/tmp/test.txt', 'rb')}
        response = requests.post('http://127.0.0.1:{}/upload'.format(self.gui.app.port), files=files)
        QtTest.QTest.qWait(2000)
        self.assertTrue(os.path.isfile('/tmp/OnionShare/test.txt'))

    @pytest.mark.run(order=20)
    def test_uploads_widget_present(self):
        '''Test that the No Uploads Yet label is hidden, that Clear History is present'''
        self.assertFalse(self.gui.receive_mode.uploads.no_uploads_label.isVisible())
        self.assertTrue(self.gui.receive_mode.uploads.clear_history_button.isVisible())

    @pytest.mark.run(order=21)
    def test_upload_count_incremented(self):
        '''Test that the Upload Count has incremented'''
        self.assertEquals(self.gui.receive_mode.uploads_completed, 1)

    @pytest.mark.run(order=22)
    def test_upload_same_file_is_renamed(self):
        '''Test that we can upload the same file and that it gets renamed'''
        files = {'file[]': open('/tmp/test.txt', 'rb')}
        response = requests.post('http://127.0.0.1:{}/upload'.format(self.gui.app.port), files=files)
        QtTest.QTest.qWait(2000)
        self.assertTrue(os.path.isfile('/tmp/OnionShare/test-2.txt'))

    @pytest.mark.run(order=23)
    def test_upload_count_incremented_again(self):
        '''Test that the Upload Count has incremented again'''
        self.assertEquals(self.gui.receive_mode.uploads_completed, 2)

    @pytest.mark.run(order=24)
    def test_server_is_stopped(self):
        '''Test that the server stops when we click Stop'''
        QtTest.QTest.mouseClick(self.gui.receive_mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEquals(self.gui.receive_mode.server_status.status, 0)

    @pytest.mark.run(order=25)
    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        QtTest.QTest.qWait(2000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=26)
    def test_server_status_indicator_says_closed(self):
        '''Test that the Server Status indicator shows we closed'''
        self.assertEquals(self.gui.receive_mode.server_status_label.text(), strings._('gui_status_indicator_receive_stopped', True))

if __name__ == "__main__":
    unittest.main()
