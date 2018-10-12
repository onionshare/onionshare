#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModePublicModeTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": True,
        }
        cls.gui = GuiShareTest.set_up(test_settings, 'LocalShareModePublicModeTest')

    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(after='test_run_all_common_setup_tests')
    def test_run_all_share_mode_tests(self):
        self.run_all_share_mode_tests(True, False)

if __name__ == "__main__":
    unittest.main()
