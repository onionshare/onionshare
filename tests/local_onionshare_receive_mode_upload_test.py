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
        cls.gui = GuiReceiveTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiReceiveTest.tear_down()

    @pytest.mark.gui
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_receive_mode_tests(False, True)

if __name__ == "__main__":
    unittest.main()
