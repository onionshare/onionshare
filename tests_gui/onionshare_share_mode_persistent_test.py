#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

class LocalShareModePersistentSlugTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "use_legacy_v2_onions": True,
            "public_mode": False,
            "slug": "",
            "save_private_key": True,
            "close_after_first_download": False,
        }
        cls.gui = TorGuiShareTest.set_up(test_settings, 'ShareModePersistentSlugTest')

    @pytest.mark.run(order=1)
    @pytest.mark.tor
    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(order=2)
    @pytest.mark.tor
    def test_run_all_share_mode_tests(self):
        self.run_all_share_mode_persistent_tests(False, True)

if __name__ == "__main__":
    unittest.main()
