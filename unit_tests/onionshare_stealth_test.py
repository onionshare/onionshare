#!/usr/bin/env python3
import os, sys, unittest, socket, pytest, json
from PyQt5 import QtCore, QtWidgets, QtTest

from onionshare import onion, strings, common
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class OnionShareGuiTest(unittest.TestCase):
    '''Test the OnionShare GUI'''
    onion_host = ''
    slug = ''

    @classmethod
    def setUpClass(cls):
        '''Create the GUI'''
        # Create our test file
        testfile = open('/tmp/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()

        # Start the Onion
        strings.load_strings(common)

        testonion = onion.Onion()
        global qtapp
        qtapp = Application()
        app = OnionShare(testonion, 0, 0)
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
            'hidservauth_string': ''
        }
        filename = '/tmp/stealth.json'
        open(filename, 'w').write(json.dumps(test_settings))

        cls.gui = OnionShareGui(testonion, qtapp, app, ['/tmp/test.txt'], filename)

    @classmethod
    def tearDownClass(cls):
        '''Clean up after tests'''
        os.remove('/tmp/test.txt')
        os.remove('/tmp/stealth.json')

    @pytest.mark.run(order=1)
    def test_gui_loaded_and_tor_bootstrapped(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    @pytest.mark.run(order=2)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)

        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.server_status.status, 1)

    @pytest.mark.run(order=3)
    def test_a_server_is_started(self):
        '''Test that the server has started'''
        # Wait for share to start
        QtTest.QTest.qWait(60000)

        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.server_status.status, 2)

    @pytest.mark.run(order=4)
    def test_copy_have_hidserv_auth_button(self):
        '''Test that the Copy HidservAuth button is shown'''
        self.assertTrue(self.gui.server_status.copy_hidservauth_button.isVisible())

    @pytest.mark.run(order=5)
    def test_hidserv_auth_string(self):
        '''Test the validity of the HidservAuth string'''
        self.assertRegex(self.gui.app.auth_string, r'HidServAuth %s [a-zA-Z1-9]' % self.gui.app.onion_host)

    @pytest.mark.run(order=6)
    def test_server_is_stopped(self):
        '''Test that we can stop the server'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        QtTest.QTest.qWait(1000)
        self.assertEqual(self.gui.server_status.status, 0)


if __name__ == "__main__":
    unittest.main()
