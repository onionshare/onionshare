#!/usr/bin/env python3
import os, sys, unittest, socket, pytest, json, locale
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

        testonion = onion.Onion()
        global qtapp
        qtapp = Application()
        app = OnionShare(testonion, 0, 0)
        test_settings = {
            'version': common.get_version(),
            'connection_type': 'socket_file',
            'control_port_address': '127.0.0.1',
            'control_port_port': 9051,
            'socks_address': '127.0.0.1',
            'socks_port': 9050,
            'socket_file_path': '/var/run/tor/control',
            'auth_type': 'no_auth',
            'auth_password': '',
            'close_after_first_download': True,
            'systray_notifications': True,
            'use_stealth': False,
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
        filename = '/tmp/locale.json'
        open(filename, 'w').write(json.dumps(test_settings))

        locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

        cls.gui = OnionShareGui(testonion, qtapp, app, ['/tmp/test.txt'], filename)

    @classmethod
    def tearDownClass(cls):
        '''Clean up after tests'''
        os.remove('/tmp/test.txt')
        os.remove('/tmp/locale.json')

    @pytest.mark.run(order=1)
    def test_gui_loaded_and_tor_bootstrapped(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    @pytest.mark.run(order=2)
    def test_french_strings_found(self):
        '''Test that we are seeing french strings'''
        self.assertEqual(self.gui.file_selection.add_button.text(), 'Ajouter')


if __name__ == "__main__":
    unittest.main()
