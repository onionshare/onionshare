import json
import os
import unittest
from PyQt5 import QtCore, QtTest

from onionshare import strings
from onionshare.common import Common
from onionshare.settings import Settings
from onionshare.onion import Onion
from onionshare_gui import Application, OnionShare
from onionshare_gui.settings_dialog import SettingsDialog


class OnionStub(object):
    def __init__(self, is_authenticated, supports_v3_onions):
        self._is_authenticated = is_authenticated
        self.supports_v3_onions = supports_v3_onions

    def is_authenticated(self):
        return self._is_authenticated


class SettingsGuiBaseTest(object):
    @staticmethod
    def set_up():
        '''Create the GUI'''

        # Default settings for the settings GUI tests
        test_settings = {
          "no_bridges": False,
          "tor_bridges_use_custom_bridges": "Bridge 1.2.3.4:56 EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE\nBridge 5.6.7.8:910 EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE\nBridge 11.12.13.14:1516 EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE\n",
        }

        # Create our test file
        testfile = open('/tmp/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()

        common = Common()
        common.settings = Settings(common)
        common.define_css()
        strings.load_strings(common)

        # Start the Onion
        testonion = Onion(common)
        global qtapp
        qtapp = Application(common)
        app = OnionShare(common, testonion, True, 0)

        for key, val in common.settings.default_settings.items():
            if key not in test_settings:
                test_settings[key] = val

        open('/tmp/settings.json', 'w').write(json.dumps(test_settings))

        gui = SettingsDialog(common, testonion, qtapp, '/tmp/settings.json', True)
        return gui

    @staticmethod
    def tear_down():
        '''Clean up after tests'''
        os.remove('/tmp/settings.json')

    def run_settings_gui_tests(self):
        self.gui.show()

        # Window is shown
        self.assertTrue(self.gui.isVisible())
        self.assertEqual(self.gui.windowTitle(), strings._('gui_settings_window_title'))

        # Check for updates button is hidden
        self.assertFalse(self.gui.check_for_updates_button.isVisible())

        # public mode is off
        self.assertFalse(self.gui.public_mode_checkbox.isChecked())
        # enable public mode
        QtTest.QTest.mouseClick(self.gui.public_mode_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.public_mode_checkbox.height()/2))
        self.assertTrue(self.gui.public_mode_checkbox.isChecked())

        # autostop timer is off
        self.assertFalse(self.gui.autostop_timer_checkbox.isChecked())
        # enable autostop timer
        QtTest.QTest.mouseClick(self.gui.autostop_timer_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.autostop_timer_checkbox.height()/2))
        self.assertTrue(self.gui.autostop_timer_checkbox.isChecked())

        # legacy mode checkbox and related widgets
        if self.gui.onion.is_authenticated():
            if self.gui.onion.supports_v3_onions:
                # legacy mode is off
                self.assertFalse(self.gui.use_legacy_v2_onions_checkbox.isChecked())
                # persistence is still available, stealth is hidden and disabled
                self.assertTrue(self.gui.save_private_key_widget.isVisible())
                self.assertFalse(self.gui.save_private_key_checkbox.isChecked())
                self.assertFalse(self.gui.use_stealth_widget.isVisible())
                self.assertFalse(self.gui.stealth_checkbox.isChecked())
                self.assertFalse(self.gui.hidservauth_copy_button.isVisible())

                # enable legacy mode
                QtTest.QTest.mouseClick(self.gui.use_legacy_v2_onions_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.use_legacy_v2_onions_checkbox.height()/2))
                self.assertTrue(self.gui.use_legacy_v2_onions_checkbox.isChecked())
                self.assertTrue(self.gui.save_private_key_checkbox.isVisible())
                self.assertTrue(self.gui.use_stealth_widget.isVisible())

                # enable persistent mode
                QtTest.QTest.mouseClick(self.gui.save_private_key_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.save_private_key_checkbox.height()/2))
                self.assertTrue(self.gui.save_private_key_checkbox.isChecked())
                # enable stealth mode
                QtTest.QTest.mouseClick(self.gui.stealth_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.stealth_checkbox.height()/2))
                self.assertTrue(self.gui.stealth_checkbox.isChecked())
                # now that stealth is enabled, we can't turn off legacy mode
                self.assertFalse(self.gui.use_legacy_v2_onions_checkbox.isEnabled())
                # disable stealth, persistence
                QtTest.QTest.mouseClick(self.gui.save_private_key_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.save_private_key_checkbox.height()/2))
                QtTest.QTest.mouseClick(self.gui.stealth_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.stealth_checkbox.height()/2))
                # legacy mode checkbox is enabled again
                self.assertTrue(self.gui.use_legacy_v2_onions_checkbox.isEnabled())
                # uncheck legacy mode
                QtTest.QTest.mouseClick(self.gui.use_legacy_v2_onions_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.use_legacy_v2_onions_checkbox.height()/2))
                # legacy options hidden again
                self.assertTrue(self.gui.save_private_key_widget.isVisible())
                self.assertFalse(self.gui.use_stealth_widget.isVisible())

                # re-enable legacy mode
                QtTest.QTest.mouseClick(self.gui.use_legacy_v2_onions_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.use_legacy_v2_onions_checkbox.height()/2))

            else:
                # legacy mode setting is hidden
                self.assertFalse(self.gui.use_legacy_v2_onions_checkbox.isVisible())
                # legacy options are showing
                self.assertTrue(self.gui.save_private_key_widget.isVisible())
                self.assertTrue(self.gui.use_stealth_widget.isVisible())

            # enable them all again so that we can see the setting stick in settings.json
            QtTest.QTest.mouseClick(self.gui.save_private_key_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.save_private_key_checkbox.height()/2))
            QtTest.QTest.mouseClick(self.gui.stealth_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.stealth_checkbox.height()/2))
        else:
            # None of the onion settings should appear
            self.assertFalse(self.gui.use_legacy_v2_onions_checkbox.isVisible())
            self.assertFalse(self.gui.save_private_key_widget.isVisible())
            self.assertFalse(self.gui.save_private_key_checkbox.isChecked())
            self.assertFalse(self.gui.use_stealth_widget.isVisible())
            self.assertFalse(self.gui.stealth_checkbox.isChecked())
            self.assertFalse(self.gui.hidservauth_copy_button.isVisible())

        # stay open toggled off, on
        self.assertTrue(self.gui.close_after_first_download_checkbox.isChecked())
        QtTest.QTest.mouseClick(self.gui.close_after_first_download_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.close_after_first_download_checkbox.height()/2))
        self.assertFalse(self.gui.close_after_first_download_checkbox.isChecked())

        # receive mode
        self.gui.data_dir_lineedit.setText('/tmp/OnionShareSettingsTest')


        # bundled mode is enabled
        self.assertTrue(self.gui.connection_type_bundled_radio.isEnabled())
        self.assertTrue(self.gui.connection_type_bundled_radio.isChecked())
        # bridge options are shown
        self.assertTrue(self.gui.connection_type_bridges_radio_group.isVisible())
        # bridges are set to custom
        self.assertFalse(self.gui.tor_bridges_no_bridges_radio.isChecked())
        self.assertTrue(self.gui.tor_bridges_use_custom_radio.isChecked())

        # switch to obfs4
        QtTest.QTest.mouseClick(self.gui.tor_bridges_use_obfs4_radio, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.tor_bridges_use_obfs4_radio.height()/2))
        self.assertTrue(self.gui.tor_bridges_use_obfs4_radio.isChecked())

        # custom bridges are hidden
        self.assertFalse(self.gui.tor_bridges_use_custom_textbox_options.isVisible())
        # other modes are unchecked but enabled
        self.assertTrue(self.gui.connection_type_automatic_radio.isEnabled())
        self.assertTrue(self.gui.connection_type_control_port_radio.isEnabled())
        self.assertTrue(self.gui.connection_type_socket_file_radio.isEnabled())
        self.assertFalse(self.gui.connection_type_automatic_radio.isChecked())
        self.assertFalse(self.gui.connection_type_control_port_radio.isChecked())
        self.assertFalse(self.gui.connection_type_socket_file_radio.isChecked())

        # enable automatic mode
        QtTest.QTest.mouseClick(self.gui.connection_type_automatic_radio, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.connection_type_automatic_radio.height()/2))
        self.assertTrue(self.gui.connection_type_automatic_radio.isChecked())
        # bundled is off
        self.assertFalse(self.gui.connection_type_bundled_radio.isChecked())
        # bridges are hidden
        self.assertFalse(self.gui.connection_type_bridges_radio_group.isVisible())

        # auth type is hidden in bundled or automatic mode
        self.assertFalse(self.gui.authenticate_no_auth_radio.isVisible())
        self.assertFalse(self.gui.authenticate_password_radio.isVisible())

        # enable control port mode
        QtTest.QTest.mouseClick(self.gui.connection_type_control_port_radio, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.connection_type_control_port_radio.height()/2))
        self.assertTrue(self.gui.connection_type_control_port_radio.isChecked())
        # automatic is off
        self.assertFalse(self.gui.connection_type_automatic_radio.isChecked())
        # auth options appear
        self.assertTrue(self.gui.authenticate_no_auth_radio.isVisible())
        self.assertTrue(self.gui.authenticate_password_radio.isVisible())

        # enable socket mode
        QtTest.QTest.mouseClick(self.gui.connection_type_socket_file_radio, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.connection_type_socket_file_radio.height()/2))
        self.assertTrue(self.gui.connection_type_socket_file_radio.isChecked())
        # control port is off
        self.assertFalse(self.gui.connection_type_control_port_radio.isChecked())
        # auth options are still present
        self.assertTrue(self.gui.authenticate_no_auth_radio.isVisible())
        self.assertTrue(self.gui.authenticate_password_radio.isVisible())

        # re-enable bundled mode
        QtTest.QTest.mouseClick(self.gui.connection_type_bundled_radio, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.connection_type_bundled_radio.height()/2))
        # go back to custom bridges
        QtTest.QTest.mouseClick(self.gui.tor_bridges_use_custom_radio, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.tor_bridges_use_custom_radio.height()/2))
        self.assertTrue(self.gui.tor_bridges_use_custom_radio.isChecked())
        self.assertTrue(self.gui.tor_bridges_use_custom_textbox.isVisible())
        self.assertFalse(self.gui.tor_bridges_use_obfs4_radio.isChecked())
        self.gui.tor_bridges_use_custom_textbox.setPlainText('94.242.249.2:83 E25A95F1DADB739F0A83EB0223A37C02FD519306\n148.251.90.59:7510 019F727CA6DCA6CA5C90B55E477B7D87981E75BC\n93.80.47.217:41727 A6A0D497D98097FCFE91D639548EE9E34C15CDD3')

        # Test that the Settings Dialog can save the settings and close itself
        QtTest.QTest.mouseClick(self.gui.save_button, QtCore.Qt.LeftButton)
        self.assertFalse(self.gui.isVisible())

        # Test our settings are reflected in the settings json
        with open('/tmp/settings.json') as f:
            data = json.load(f)

        self.assertTrue(data["public_mode"])
        self.assertTrue(data["autostop_timer"])

        if self.gui.onion.is_authenticated():
            if self.gui.onion.supports_v3_onions:
                self.assertTrue(data["use_legacy_v2_onions"])
            self.assertTrue(data["save_private_key"])
            self.assertTrue(data["use_stealth"])
        else:
            self.assertFalse(data["use_legacy_v2_onions"])
            self.assertFalse(data["save_private_key"])
            self.assertFalse(data["use_stealth"])

        self.assertEqual(data["data_dir"], "/tmp/OnionShareSettingsTest")
        self.assertFalse(data["close_after_first_download"])
        self.assertEqual(data["connection_type"], "bundled")
        self.assertFalse(data["tor_bridges_use_obfs4"])
        self.assertEqual(data["tor_bridges_use_custom_bridges"], "Bridge 94.242.249.2:83 E25A95F1DADB739F0A83EB0223A37C02FD519306\nBridge 148.251.90.59:7510 019F727CA6DCA6CA5C90B55E477B7D87981E75BC\nBridge 93.80.47.217:41727 A6A0D497D98097FCFE91D639548EE9E34C15CDD3\n")
