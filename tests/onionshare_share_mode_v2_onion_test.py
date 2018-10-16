#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

class ShareModeV2OnionTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "use_legacy_v2_onions": True,
        }
        cls.gui = TorGuiShareTest.set_up(test_settings, 'ShareModeV2OnionTest')

    @classmethod
    def tearDownClass(cls):
        TorGuiShareTest.tear_down()

    @pytest.mark.tor
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_tests(False, False)
        self.have_v2_onion()

if __name__ == "__main__":
    unittest.main()
