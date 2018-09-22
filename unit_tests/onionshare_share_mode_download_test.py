#!/usr/bin/env python3
import os
import sys
import unittest
import socket
import pytest
import zipfile
import socks
import json

from PyQt5 import QtCore, QtWidgets, QtTest, QtGui

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
            "public_mode": False,
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
    def test_file_selection_widget_has_a_file(self):
        '''Test that the number of files in the list is 1'''
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), 1)

    @pytest.mark.run(order=6)
    def test_info_widget_is_visible(self):
        '''Test that the info widget along top of screen is shown because we have a file'''
        self.assertTrue(self.gui.share_mode.info_widget.isVisible())

    @pytest.mark.run(order=7)
    def test_downloads_section_is_visible(self):
        '''Test that the Downloads section is visible and that the No Downloads Yet label is present'''
        self.assertTrue(self.gui.share_mode.downloads.isVisible())
        self.assertTrue(self.gui.share_mode.downloads.no_downloads_label.isVisible())

    @pytest.mark.run(order=8)
    def test_deleting_only_file_hides_delete_button(self):
        '''Test that clicking on the file item shows the delete button. Test that deleting the only item in the list hides the delete button'''
        rect = self.gui.share_mode.server_status.file_selection.file_list.visualItemRect(self.gui.share_mode.server_status.file_selection.file_list.item(0))
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.viewport(), QtCore.Qt.LeftButton, pos=rect.center())
        # Delete button should be visible
        self.assertTrue(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())
        # Click delete, and since there's no more files, the delete button should be hidden
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.delete_button, QtCore.Qt.LeftButton)
        self.assertFalse(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())

    @pytest.mark.run(order=9)
    def test_add_a_file_and_delete_using_its_delete_widget(self):
        '''Test that we can also delete a file by clicking on its [X] widget'''
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/etc/hosts')
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.item(0).item_button, QtCore.Qt.LeftButton)
        self.assertEquals(self.gui.share_mode.server_status.file_selection.get_num_files(), 0)

    @pytest.mark.run(order=10)
    def test_file_selection_widget_readd_files(self):
        '''Re-add some files to the list so we can share'''
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/etc/hosts')
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/tmp/test.txt')
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), 2)

    @pytest.mark.run(order=11)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)

        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.share_mode.server_status.status, 1)

    @pytest.mark.run(order=12)
    def test_server_status_indicator_says_starting(self):
        '''Test that the Server Status indicator shows we are Starting'''
        self.assertEquals(self.gui.share_mode.server_status_label.text(), strings._('gui_status_indicator_share_working', True))

    @pytest.mark.run(order=13)
    def test_add_delete_buttons_now_hidden(self):
        '''Test that the add and delete buttons are hidden when the server starts'''
        self.assertFalse(self.gui.share_mode.server_status.file_selection.add_button.isVisible())
        self.assertFalse(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())

    @pytest.mark.run(order=14)
    def test_settings_button_is_hidden(self):
        '''Test that the settings button is hidden when the server starts'''
        self.assertFalse(self.gui.settings_button.isVisible())

    @pytest.mark.run(order=15)
    def test_a_server_is_started(self):
        '''Test that the server has started'''
        QtTest.QTest.qWait(2000)
        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.share_mode.server_status.status, 2)

    @pytest.mark.run(order=16)
    def test_a_web_server_is_running(self):
        '''Test that the web server has started'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.assertEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    # Running in local mode, so we have no .onion
    #@pytest.mark.run(order=17)
    #def test_have_an_onion_service(self):
    #    '''Test that we have a valid Onion URL'''
    #    self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')
    #    self.assertEqual(len(self.gui.app.onion_host), 62)

    @pytest.mark.run(order=18)
    def test_have_a_slug(self):
        '''Test that we have a valid slug'''
        self.assertRegex(self.gui.share_mode.server_status.web.slug, r'(\w+)-(\w+)')

    @pytest.mark.run(order=19)
    def test_url_description_shown(self):
        '''Test that the URL label is showing'''
        self.assertTrue(self.gui.share_mode.server_status.url_description.isVisible())

    @pytest.mark.run(order=20)
    def test_have_copy_url_button(self):
        '''Test that the Copy URL button is shown and can be copied to clipboard'''
        self.assertTrue(self.gui.share_mode.server_status.copy_url_button.isVisible())
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.copy_url_button, QtCore.Qt.LeftButton)
        clipboard = self.gui.qtapp.clipboard()
        self.assertEquals(clipboard.text(), 'http://127.0.0.1:{}/{}'.format(self.gui.app.port, self.gui.share_mode.server_status.web.slug))

    @pytest.mark.run(order=21)
    def test_server_status_indicator_says_sharing(self):
        '''Test that the Server Status indicator shows we are Sharing'''
        self.assertEquals(self.gui.share_mode.server_status_label.text(), strings._('gui_status_indicator_share_started', True))

    @pytest.mark.run(order=22)
    def test_web_page(self):
        '''Test that the web page contains the term Total size'''
        s = socks.socksocket()
        s.settimeout(60)
        s.connect(('127.0.0.1', self.gui.app.port))

        http_request = 'GET {} HTTP/1.0\r\n'.format(self.gui.share_mode.server_status.web.slug)
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
        self.assertTrue('Total size' in f.read())
        f.close()

    @pytest.mark.run(order=23)
    def test_download_share(self):
        '''Test that we can download the share'''
        s = socks.socksocket()
        s.settimeout(60)
        s.connect(('127.0.0.1', self.gui.app.port))

        http_request = 'GET {}/download HTTP/1.0\r\n'.format(self.gui.share_mode.server_status.web.slug)
        http_request += 'Host: 127.0.0.1\r\n'
        http_request += '\r\n'
        s.sendall(http_request.encode('utf-8'))

        with open('/tmp/download.zip', 'wb') as file_to_write:
            while True:
               data = s.recv(1024)
               if not data:
                   break
               file_to_write.write(data)
            file_to_write.close()

        zip = zipfile.ZipFile('/tmp/download.zip')
        self.assertEquals('onionshare', zip.read('test.txt').decode('utf-8'))

    @pytest.mark.run(order=24)
    def test_downloads_widget_present(self):
        QtTest.QTest.qWait(1000)
        '''Test that the No Downloads Yet label is hidden, that Clear History is present'''
        self.assertFalse(self.gui.share_mode.downloads.no_downloads_label.isVisible())
        self.assertTrue(self.gui.share_mode.downloads.clear_history_button.isVisible())

    @pytest.mark.run(order=25)
    def test_server_is_stopped(self):
        '''Test that the server stopped automatically when we downloaded the share'''
        self.assertEquals(self.gui.share_mode.server_status.status, 0)

    @pytest.mark.run(order=26)
    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=27)
    def test_server_status_indicator_says_closed(self):
        '''Test that the Server Status indicator shows we closed because download occurred'''
        self.assertEquals(self.gui.share_mode.server_status_label.text(), strings._('closing_automatically', True))

    @pytest.mark.run(order=28)
    def test_add_button_visible_again(self):
        '''Test that the add button should be visible again'''
        self.assertTrue(self.gui.share_mode.server_status.file_selection.add_button.isVisible())


if __name__ == "__main__":
    unittest.main()
