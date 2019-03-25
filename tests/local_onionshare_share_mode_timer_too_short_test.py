#!/usr/bin/env python3
import pytest
import unittest
from PyQt5 import QtCore, QtTest

from .GuiShareTest import GuiShareTest

class LocalShareModeTimerTooShortTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "autostop_timer": True,
        }
        cls.gui = GuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    @pytest.mark.gui
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests()
        # Set a low timeout
        self.set_timeout(self.gui.share_mode, 2)
        QtTest.QTest.qWait(3000)
        QtCore.QTimer.singleShot(4000, self.accept_dialog)
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.share_mode.server_status.status, 0)

if __name__ == "__main__":
    unittest.main()
