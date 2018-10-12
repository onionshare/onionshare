#!/usr/bin/env python3
import pytest
import unittest

from .GuiReceiveTest import GuiReceiveTest

class LocalReceiveModePublicModeTest(unittest.TestCase, GuiReceiveTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": True,
            "receive_allow_receiver_shutdown": True
        }
        cls.gui = GuiReceiveTest.set_up(test_settings, 'LocalReceiveModePublicModeTest')

    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(after='test_run_all_common_setup_tests')
    def test_run_all_receive_mode_tests(self):
        self.run_all_receive_mode_tests(True, True)

if __name__ == "__main__":
    unittest.main()
