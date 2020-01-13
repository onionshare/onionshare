#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest


class ShareModePersistentPasswordTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "use_legacy_v2_onions": True,
            "public_mode": False,
            "password": "",
            "save_private_key": True,
            "close_after_first_download": False,
        }
        cls.gui = TorGuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        TorGuiShareTest.tear_down()

    @pytest.mark.gui
    @pytest.mark.tor
    @pytest.mark.skipif(pytest.__version__ < "2.9", reason="requires newer pytest")
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_persistent_tests(False, True)


if __name__ == "__main__":
    unittest.main()
