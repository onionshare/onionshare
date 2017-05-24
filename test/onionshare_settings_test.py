#!/usr/bin/env python3
import os, sys, unittest, inspect, json
from PyQt5 import QtCore, QtWidgets, QtGui, QtTest

sys.path.append('../onionshare')
sys.path.append('../onionshare_gui')

setattr(sys, 'onionshare_dev_mode', True)

from onionshare import onion, strings, common
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class OnionShareSettingsTest(unittest.TestCase):
    '''Test the OnionShare Settings Dialog'''
    @classmethod
    def setUpClass(cls):
        '''Create the GUI'''

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
        '''
        Test that:
        1. we can unset the stay_open variable,
        2. that saving the settings dialog writes the correct new setting to the json file,
        3. that saving the dialog reboots the onion Tor connection
        '''
        QtTest.QTest.mouseClick(self.gui.close_after_first_download_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.close_after_first_download_checkbox.height()/2))
        self.assertFalse(self.gui.close_after_first_download_checkbox.isChecked())

        QtTest.QTest.mouseClick(self.gui.save_button, QtCore.Qt.LeftButton)
        jsondata = open(os.path.expanduser('~/.config/onionshare/onionshare.json')).read()
        config = json.loads(jsondata)
        self.assertFalse(config['close_after_first_download'])

        self.assertTrue(self.gui.onion.connected_to_tor)
         

if __name__ == "__main__":
    unittest.main()
