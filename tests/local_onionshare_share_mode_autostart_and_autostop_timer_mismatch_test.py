#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModeAutoStartTimerTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "autostart_timer": True,
            "autostop_timer": True,
        }
        cls.gui = GuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    @pytest.mark.gui
    @pytest.mark.skipif(pytest.__version__ < '2.9', reason="requires newer pytest")
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_autostop_autostart_mismatch_tests(False)

if __name__ == "__main__":
    unittest.main()
