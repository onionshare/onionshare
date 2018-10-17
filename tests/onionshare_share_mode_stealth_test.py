#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

class ShareModeStealthTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "use_legacy_v2_onions": True,
            "use_stealth": True,
        }
        cls.gui = TorGuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        TorGuiShareTest.tear_down()

    @pytest.mark.tor
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(False)
        self.hidserv_auth_string()
        self.copy_have_hidserv_auth_button(self.gui.share_mode)

if __name__ == "__main__":
    unittest.main()
