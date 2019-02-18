#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiReceiveTest import TorGuiReceiveTest

class ReceiveModeTest(unittest.TestCase, TorGuiReceiveTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "receive_allow_receiver_shutdown": True
        }
        cls.gui = TorGuiReceiveTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        TorGuiReceiveTest.tear_down()

    @pytest.mark.gui
    @pytest.mark.tor
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_receive_mode_tests(False, True)

if __name__ == "__main__":
    unittest.main()
