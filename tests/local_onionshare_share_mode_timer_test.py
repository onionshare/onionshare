#!/usr/bin/env python3
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModeTimerTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "shutdown_timeout": True,
        }
        cls.gui = GuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_timer_tests(False)

if __name__ == "__main__":
    unittest.main()
