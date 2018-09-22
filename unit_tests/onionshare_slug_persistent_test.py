#!/usr/bin/env python3
import os
import sys
import unittest
import socket
import pytest
import zipfile
import socks
import json

from PyQt5 import QtCore, QtWidgets, QtTest

from onionshare.common import Common
from onionshare.web import Web
from onionshare import onion, strings
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class OnionShareGuiTest(unittest.TestCase):
    '''Test the OnionShare GUI'''
    slug = ''

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
            "public_mode": False,
            "receive_allow_receiver_shutdown": True,
            "save_private_key": True,
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

    @pytest.mark.run(order=1)
    def test_gui_loaded(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    @pytest.mark.run(order=2)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)

        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.share_mode.server_status.status, 1)

    @pytest.mark.run(order=3)
    def test_server_status_indicator_says_starting(self):
        '''Test that the Server Status indicator shows we are Starting'''
        self.assertEquals(self.gui.share_mode.server_status_label.text(), strings._('gui_status_indicator_share_working', True))

    @pytest.mark.run(order=4)
    def test_a_server_is_started(self):
        '''Test that the server has started'''
        QtTest.QTest.qWait(2000)
        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.share_mode.server_status.status, 2)

    @pytest.mark.run(order=5)
    def test_a_web_server_is_running(self):
        '''Test that the web server has started'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.assertEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=6)
    def test_have_a_slug(self):
        '''Test that we have a valid slug'''
        self.assertRegex(self.gui.share_mode.server_status.web.slug, r'(\w+)-(\w+)')
        global slug
        slug = self.gui.share_mode.server_status.web.slug

    @pytest.mark.run(order=7)
    def test_server_can_be_stopped(self):
        '''Test we can stop the service'''
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)

        # Should be in SERVER_STOPPED state
        self.assertEqual(self.gui.share_mode.server_status.status, 0)

    @pytest.mark.run(order=8)
    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        QtTest.QTest.qWait(4000)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=9)
    def test_server_started_again(self):
        '''Test we can start the service again'''
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)
        QtTest.QTest.qWait(2000)
        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.share_mode.server_status.status, 2)

    @pytest.mark.run(order=10)
    def test_have_same_slug(self):
        '''Test that we have the same slug'''
        self.assertEqual(self.gui.share_mode.server_status.web.slug, slug)

    @pytest.mark.run(order=11)
    def test_server_is_stopped_again(self):
        '''Test that we can stop the server'''
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)
        QtTest.QTest.qWait(1000)
        self.assertEqual(self.gui.share_mode.server_status.status, 0)

if __name__ == "__main__":
    unittest.main()
