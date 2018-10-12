#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

class ShareModeCancelTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = TorGuiShareTest.set_up(test_settings, 'ShareModeCancelTest')

    @pytest.mark.run(order=1)
    @pytest.mark.tor
    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(order=2)
    @pytest.mark.tor
    def test_run_share_mode_setup_tests(self):
        self.run_all_share_mode_setup_tests()

    @pytest.mark.run(order=3)
    @pytest.mark.tor
    def test_cancel_the_share(self):
        self.cancel_the_share(self.gui.share_mode)

if __name__ == "__main__":
    unittest.main()
