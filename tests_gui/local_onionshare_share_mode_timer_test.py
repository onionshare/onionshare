#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModeTimerTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "shutdown_timeout": True,
        }
        cls.gui = GuiShareTest.set_up(test_settings, 'LocalShareModeTimerTest')

    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(after='test_run_all_common_setup_tests')
    def test_run_all_share_mode_timer_tests(self):
        self.run_all_share_mode_timer_tests(False)

if __name__ == "__main__":
    unittest.main()
