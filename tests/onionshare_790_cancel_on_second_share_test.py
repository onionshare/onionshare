#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

# Tests #790 regression
class ShareModeCancelSecondShareTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "close_after_first_download": True 
        }
        cls.gui = TorGuiShareTest.set_up(test_settings, 'ShareModeCancelSecondShareTest')

    @pytest.mark.tor
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_tests(False, False)
        self.cancel_the_share(self.gui.share_mode)
        self.server_is_stopped(self.gui.share_mode, False)
        self.web_server_is_stopped()

if __name__ == "__main__":
    unittest.main()
