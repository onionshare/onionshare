#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModeCancelTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
           "autostart_timer": True,
        }
        cls.gui = GuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    @pytest.mark.gui
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests()
        self.cancel_the_share(self.gui.share_mode)

if __name__ == "__main__":
    unittest.main()
