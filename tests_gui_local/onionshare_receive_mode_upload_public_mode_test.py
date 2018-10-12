#!/usr/bin/env python3
import pytest
import unittest

from .GuiReceiveTest import GuiReceiveTest

class ReceiveModePublicModeTest(unittest.TestCase, GuiReceiveTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": True,
            "receive_allow_receiver_shutdown": True
        }
        cls.gui = GuiReceiveTest.set_up(test_settings, 'ReceiveModePublicModeTest')

    @classmethod
    def tearDownClass(cls):
        GuiReceiveTest.tear_down()

    @pytest.mark.run(order=1)
    def test_run_all_common_setup_tests(self):
        GuiReceiveTest.run_all_common_setup_tests(self)

    @pytest.mark.run(order=2)
    def test_run_all_receive_mode_tests(self):
        GuiReceiveTest.run_all_receive_mode_tests(self, True, True)

if __name__ == "__main__":
    unittest.main()
