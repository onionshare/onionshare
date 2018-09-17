#!/usr/bin/env python3
import os, sys, unittest, socket, pytest, json
from PyQt5 import QtCore, QtWidgets, QtTest

from onionshare import onion, strings, common
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

        # Start the Onion
        strings.load_strings(common)

        test_settings = {
            'version': common.get_version(),
            'connection_type': 'bundled',
            'control_port_address': '127.0.0.1',
            'control_port_port': 9051,
            'socks_address': '127.0.0.1',
            'socks_port': 9050,
            'socket_file_path': '/var/run/tor/control',
            'auth_type': 'no_auth',
            'auth_password': '',
            'close_after_first_download': True,
            'systray_notifications': True,
            'use_stealth': True,
            'use_autoupdate': True,
            'autoupdate_timestamp': None,
            'no_bridges': True,
            'tor_bridges_use_obfs4': False,
            'tor_bridges_use_custom_bridges': '',
            'save_private_key': False,
            'private_key': '',
            'slug': '',
            'hidservauth_string': '',
            'shutdown_timeout': True
        }
        filename = '/tmp/stealth.json'
        open(filename, 'w').write(json.dumps(test_settings))

        testonion = onion.Onion()
        global qtapp
        qtapp = Application()
        app = OnionShare(testonion, 0, 0)
        cls.gui = OnionShareGui(testonion, qtapp, app, ['/tmp/test.txt'], filename)

    @classmethod
    def tearDownClass(cls):
        '''Clean up after tests'''
        os.remove('/tmp/test.txt')

    @pytest.mark.run(order=1)
    def test_gui_loaded_and_tor_bootstrapped(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    @pytest.mark.run(order=2)
    def test_set_timeout(self):
        '''Test that the timeout can be set'''
        timer = QtCore.QDateTime.currentDateTime().addSecs(120)
        self.gui.server_status.shutdown_timeout.setDateTime(timer)
        self.assertTrue(self.gui.server_status.shutdown_timeout.dateTime(), timer)

    @pytest.mark.run(order=3)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.server_status.status, 1)

    @pytest.mark.run(order=4)
    def test_server_is_started(self):
        '''Test that the server has started'''
        # Wait for share to start
        QtTest.QTest.qWait(60000)

        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.server_status.status, 2)

    @pytest.mark.run(order=5)
    def test_timeout_widget_hidden(self):
        '''Test that the timeout widget is hidden when share has started'''
        self.assertFalse(self.gui.server_status.shutdown_timeout_container.isVisible())

    @pytest.mark.run(order=6)
    def test_server_timed_out(self):
        '''Test that the server has timed out after the timer ran out'''
        QtTest.QTest.qWait(63000)
        # We should have timed out now
        self.assertEqual(self.gui.server_status.status, 0)

    @pytest.mark.run(order=7)
    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

if __name__ == "__main__":
    unittest.main()
