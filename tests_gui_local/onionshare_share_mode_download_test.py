#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class ShareModeTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = GuiShareTest.set_up(test_settings, 'ShareModeTest')

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    @pytest.mark.run(order=1)
    def test_run_all_common_setup_tests(self):
        GuiShareTest.run_all_common_setup_tests(self)

    @pytest.mark.run(order=2)
    def test_run_all_share_mode_tests(self):
        GuiShareTest.run_all_share_mode_tests(self, False, False)

if __name__ == "__main__":
    unittest.main()
