#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class ShareModeStayOpenTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "close_after_first_download": False,
        }
        cls.gui = GuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    @pytest.mark.run(order=1)
    def test_run_all_common_setup_tests(self):
        GuiShareTest.run_all_common_setup_tests(self)

    @pytest.mark.run(order=2)
    def test_run_all_share_mode_tests(self):
        GuiShareTest.run_all_share_mode_tests(self, False, True)

if __name__ == "__main__":
    unittest.main()
