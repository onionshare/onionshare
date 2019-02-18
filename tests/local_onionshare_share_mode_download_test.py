#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModeTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = GuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    @pytest.mark.gui
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_tests(False, False)

if __name__ == "__main__":
    unittest.main()
