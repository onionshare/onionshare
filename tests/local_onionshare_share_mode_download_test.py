#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModeTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = GuiShareTest.set_up(test_settings, 'LocalShareModeTest')

    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(after='test_run_all_common_setup_tests')
    def test_run_all_share_mode_tests(self):
        self.run_all_share_mode_tests(False, False)

if __name__ == "__main__":
    unittest.main()
