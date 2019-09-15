#!/usr/bin/env python3
import pytest
import unittest

from .GuiReceiveTest import GuiReceiveTest

class LocalReceiveModeClearAllButtonTest(unittest.TestCase, GuiReceiveTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = GuiReceiveTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiReceiveTest.tear_down()

    @pytest.mark.gui
    @pytest.mark.skipif(pytest.__version__ < '2.9', reason="requires newer pytest")
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_clear_all_button_tests(False)

if __name__ == "__main__":
    unittest.main()
