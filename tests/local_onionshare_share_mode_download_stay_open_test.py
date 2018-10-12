#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModeStayOpenTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "close_after_first_download": False,
        }
        cls.gui = GuiShareTest.set_up(test_settings, 'LocalShareModeStayOpenTest')

    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(after='test_run_all_common_setup_tests')
    def test_run_all_share_mode_tests(self):
        self.run_all_share_mode_tests(False, True)

if __name__ == "__main__":
    unittest.main()
