#!/usr/bin/env python3
import pytest
import unittest

from .GuiReceiveTest import GuiReceiveTest

class LocalReceiveModeTest(unittest.TestCase, GuiReceiveTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "receive_allow_receiver_shutdown": True
        }
        cls.gui = GuiReceiveTest.set_up(test_settings, 'LocalReceiveModeTest')

    @pytest.mark.run(order=1)
    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(order=2)
    def test_run_all_receive_mode_tests(self):
        self.run_all_receive_mode_tests(False, True)

if __name__ == "__main__":
    unittest.main()
