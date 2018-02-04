#!/usr/bin/env python3
import os, sys, unittest, socket, pytest, json
from PyQt5 import QtCore, QtWidgets, QtTest

from onionshare import onion, strings, common
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class SettingsDialogTest(unittest.TestCase):
    '''Test the SettingsDialog GUI'''
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
            'close_after_first_download': False,
            'systray_notifications': True,
            'use_stealth': False,
            'use_autoupdate': True,
            'autoupdate_timestamp': None,
            'no_bridges': True,
            'tor_bridges_use_obfs4': False,
            'tor_bridges_use_custom_bridges': '',
            'save_private_key': True,
            'private_key': '',
            'slug': '',
            'hidservauth_string': ''
        }
        filename = '/tmp/stay_open.json'
        open(filename, 'w').write(json.dumps(test_settings))

        cls.gui = onionshare_gui.SettingsDialog(testonion, qtapp, config=filename)

    @classmethod
    def tearDownClass(cls):
        '''Clean up after tests'''
        os.remove('/tmp/test.txt')

    @pytest.mark.run(order=1)
    def test_settings_dialog_clicked(self):
        '''Test the Settings Dialog is shown'''
        self.assertEqual(self.gui.windowTitle(), strings._('gui_settings_window_title', True))

    @pytest.mark.run(order=2)
    def test_check_for_updates_button_is_hidden(self):
        '''Test that the check_for_updates button is hidden because this is a Linux machine'''
        self.assertFalse(self.gui.check_for_updates_button.isVisible())

    @pytest.mark.run(order=3)
    def test_server_stay_open_checkbox_is_unchecked(self):
        '''Test that the Close Automatically setting is not Checked'''
        self.assertFalse(self.gui.close_after_first_download_checkbox.isChecked())

    @pytest.mark.run(order=4)
    def test_server_stay_open_checkbox_button_pressed(self):
        '''Test we can check the Close Automatically checkbox'''
        QtTest.QTest.mouseClick(self.gui.close_after_first_download_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.close_after_first_download_checkbox.height()/2))
        self.assertTrue(self.gui.close_after_first_download_checkbox.isChecked())

    @pytest.mark.run(order=5)
    def test_save_settings(self):
        '''Test that the Settings Dialog can save the settings and close itself'''
        QtTest.QTest.mouseClick(self.gui.save_button, QtCore.Qt.LeftButton)
        self.assertFalse(self.gui.isVisible())

    @pytest.mark.run(order=6)
    def test_stay_open_setting_found_in_json(self):
        '''Test that the Close Automatically setting is now set to true in the settings json'''
        self.assertTrue('"close_after_first_download": true' in open('/tmp/stay_open.json').read())


if __name__ == "__main__":
    unittest.main()
