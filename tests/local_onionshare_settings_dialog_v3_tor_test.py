#!/usr/bin/env python3
import json
import unittest
from PyQt5 import QtCore, QtTest

from onionshare import strings
from .SettingsGuiBaseTest import SettingsGuiBaseTest, OnionStub


class SettingsGuiTest(unittest.TestCase, SettingsGuiBaseTest):
    @classmethod
    def setUpClass(cls):
        cls.gui = SettingsGuiBaseTest.set_up()

    @classmethod
    def tearDownClass(cls):
        SettingsGuiBaseTest.tear_down()

    def test_gui_v3_tor(self):
        self.gui.onion = OnionStub(True, True)
        self.gui.reload_settings()
        self.run_settings_gui_tests()


if __name__ == "__main__":
    unittest.main()
