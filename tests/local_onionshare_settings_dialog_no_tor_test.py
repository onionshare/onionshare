#!/usr/bin/env python3
import pytest
import unittest

from onionshare import strings
from .SettingsGuiBaseTest import SettingsGuiBaseTest, OnionStub


class SettingsGuiTest(unittest.TestCase, SettingsGuiBaseTest):
    @classmethod
    def setUpClass(cls):
        cls.gui = SettingsGuiBaseTest.set_up()

    @classmethod
    def tearDownClass(cls):
        SettingsGuiBaseTest.tear_down()

    @pytest.mark.gui
    @pytest.mark.skipif(pytest.__version__ < '2.9', reason="requires newer pytest")
    def test_gui_no_tor(self):
        self.gui.onion = OnionStub(False, False)
        self.gui.reload_settings()
        self.run_settings_gui_tests()


if __name__ == "__main__":
    unittest.main()
