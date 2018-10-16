#!/usr/bin/env python3
import unittest

from .GuiReceiveTest import GuiReceiveTest

class LocalReceiveModeTimerTest(unittest.TestCase, GuiReceiveTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "shutdown_timeout": True,
        }
        cls.gui = GuiReceiveTest.set_up(test_settings, 'LocalReceiveModeTimerTest')

    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_receive_mode_timer_tests(False)

if __name__ == "__main__":
    unittest.main()
