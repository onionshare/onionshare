#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

class ShareModeTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = TorGuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        TorGuiShareTest.tear_down()

    @pytest.mark.tor
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_tests(False, False)

if __name__ == "__main__":
    unittest.main()
