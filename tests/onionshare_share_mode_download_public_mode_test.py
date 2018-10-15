#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

class ShareModePublicModeTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": True,
        }
        cls.gui = TorGuiShareTest.set_up(test_settings, 'ShareModePublicModeTest')

    @pytest.mark.tor
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_tests(True, False)

if __name__ == "__main__":
    unittest.main()
