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
            'systray_notifications': False,
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
        filename = '/tmp/settings.json'
        open(filename, 'w').write(json.dumps(test_settings))

        cls.gui = onionshare_gui.SettingsDialog(testonion, qtapp, config=filename)

    @classmethod
    def tearDownClass(cls):
        '''Clean up after tests'''
        os.remove('/tmp/settings.json')

    @pytest.mark.run(order=1)
    def test_settings_dialog_clicked(self):
        '''Test the Settings Dialog is shown'''
        self.assertEqual(self.gui.windowTitle(), strings._('gui_settings_window_title', True))

    @pytest.mark.run(order=2)
    def test_autoupdate_group_is_hidden(self):
        '''Test that the autoupdate widgets are hidden because this is a Linux machine'''
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
    def test_systray_notifications_checkbox_is_unchecked(self):
        '''Test that the systray_notifications_checkbox is not Checked'''
        self.assertFalse(self.gui.systray_notifications_checkbox.isChecked())

    @pytest.mark.run(order=6)
    def test_systray_notifications_checkbox_button_pressed(self):
        '''Test we can check the systray_notifications_checkbox checkbox'''
        QtTest.QTest.mouseClick(self.gui.systray_notifications_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.systray_notifications_checkbox.height()/2))
        self.assertTrue(self.gui.systray_notifications_checkbox.isChecked())

    @pytest.mark.run(order=7)
    def test_save_private_key_checkbox_is_unchecked(self):
        '''Test that the save_private_key_checkbox is not Checked'''
        self.assertFalse(self.gui.save_private_key_checkbox.isChecked())

    @pytest.mark.run(order=8)
    def test_save_private_key_checkbox_button_pressed(self):
        '''Test we can check the save_private_key_checkbox checkbox'''
        QtTest.QTest.mouseClick(self.gui.save_private_key_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.save_private_key_checkbox.height()/2))
        self.assertTrue(self.gui.save_private_key_checkbox.isChecked())

    @pytest.mark.run(order=9)
    def test_stealth_checkbox_is_unchecked(self):
        '''Test that the stealth_checkbox is not Checked'''
        self.assertFalse(self.gui.stealth_checkbox.isChecked())

    @pytest.mark.run(order=10)
    def test_stealth_checkbox_button_pressed(self):
        '''Test we can check the stealth_checkbox checkbox'''
        QtTest.QTest.mouseClick(self.gui.stealth_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.stealth_checkbox.height()/2))
        self.assertTrue(self.gui.stealth_checkbox.isChecked())

    @pytest.mark.run(order=11)
    def test_hidservauth_button_hidden(self):
        '''Test that the HidServAuth copy button is hidden'''
        self.assertFalse(self.gui.hidservauth_copy_button.isVisible())

    @pytest.mark.run(order=12)
    def test_bundled_tor_radio_enabled(self):
        '''Test that the Bundled Tor connection method is enabled and set'''
        self.assertTrue(self.gui.connection_type_bundled_radio.isEnabled())
        self.assertTrue(self.gui.connection_type_bundled_radio.isChecked())

    @pytest.mark.run(order=13)
    def test_custom_bridges_textbox_hidden(self):
        '''Test that the custom Bridges textbox is hidden (no bridges are yet in use)'''
        self.assertFalse(self.gui.tor_bridges_use_custom_textbox_options.isVisible())

    @pytest.mark.run(order=14)
    def test_save_settings(self):
        '''Test that the Settings Dialog can save the settings and close itself'''
        QtTest.QTest.mouseClick(self.gui.save_button, QtCore.Qt.LeftButton)
        self.assertFalse(self.gui.isVisible())

    @pytest.mark.run(order=16)
    def test_settings_found_in_json(self):
        '''Test that the various settings we changed, are updated in the settings json'''
        self.assertTrue('"close_after_first_download": true' in open('/tmp/settings.json').read())
        self.assertTrue('"systray_notifications": true' in open('/tmp/settings.json').read())
        self.assertTrue('"save_private_key": true' in open('/tmp/settings.json').read())
        self.assertTrue('"use_stealth": true' in open('/tmp/settings.json').read())

if __name__ == "__main__":
    unittest.main()
