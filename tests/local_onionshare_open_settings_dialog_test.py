#!/usr/bin/env python3
import unittest
from PyQt5 import QtCore, QtTest

from .GuiShareTest import GuiShareTest

class LocalOpenSettingsDialogTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = GuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests()
        # Make sure we can open the settings dialog via the settings button
        QtCore.QTimer.singleShot(1000, self.accept_dialog)
        QtTest.QTest.mouseClick(self.gui.settings_button, QtCore.Qt.LeftButton)

if __name__ == "__main__":
    unittest.main()
