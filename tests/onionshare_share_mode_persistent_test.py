#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

class ShareModePersistentSlugTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "use_legacy_v2_onions": True,
            "public_mode": False,
            "slug": "",
            "save_private_key": True,
            "close_after_first_download": False,
        }
        cls.gui = TorGuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        TorGuiShareTest.tear_down()

    @pytest.mark.gui
    @pytest.mark.tor
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_persistent_tests(False, True)

if __name__ == "__main__":
    unittest.main()
