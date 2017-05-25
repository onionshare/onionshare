#!/usr/bin/env python3
import os, sys, unittest, inspect, json
from PyQt5 import QtCore, QtWidgets, QtGui, QtTest

from onionshare import onion, strings, common
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class OnionShareSettingsTest(unittest.TestCase):
    '''Test the OnionShare Settings Dialog'''
    @classmethod
    def setUpClass(cls):
        '''Create the GUI'''
        # Wipe settings
        try:
            os.remove(os.path.expanduser('~/.config/onionshare/onionshare.json'))
        except OSError:
            pass

        # Start the Onion
        strings.load_strings(common)

        testonion = onion.Onion()
        global qtapp
        qtapp = Application()
        app = OnionShare(testonion, 0, 0)
        cls.gui = onionshare_gui.SettingsDialog(testonion, qtapp)

    def test_guiLoaded(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    def test_settingsButtonPress(self):
        '''Test that we can unset the stay_open var, that it writes the json to file correctly, and reloads settings/tor'''
        QtTest.QTest.mouseClick(self.gui.close_after_first_download_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.close_after_first_download_checkbox.height()/2))
        self.assertFalse(self.gui.close_after_first_download_checkbox.isChecked())

        QtTest.QTest.mouseClick(self.gui.save_button, QtCore.Qt.LeftButton)
        jsondata = open(os.path.expanduser('~/.config/onionshare/onionshare.json')).read()
        config = json.loads(jsondata)
        self.assertFalse(config['close_after_first_download'])

        self.assertTrue(self.gui.onion.connected_to_tor)


if __name__ == "__main__":
    unittest.main()
