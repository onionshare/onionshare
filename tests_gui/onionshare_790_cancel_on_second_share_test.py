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

    @pytest.mark.run(order=1)
    @pytest.mark.tor
    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(order=2)
    @pytest.mark.tor
    def test_run_share_mode_tests(self):
        self.run_all_share_mode_tests(False, False)

    # Stop the share in order to test canceling the next share
    #@pytest.mark.run(order=3)
    #@pytest.mark.tor
    #def test_stop_share(self):
    #    self.server_is_stopped(self.gui.share_mode, True)
    #    self.web_service_is_stopped()

    @pytest.mark.run(order=4)
    @pytest.mark.tor
    def test_cancel_the_share(self):
        self.cancel_the_share(self.gui.share_mode)

    @pytest.mark.run(order=5)
    @pytest.mark.tor
    def test_server_is_stopped_round2(self):
        self.server_is_stopped(self.gui.share_mode, False)

    @pytest.mark.run(order=6)
    @pytest.mark.tor
    def test_web_service_is_stopped_round2(self):
        self.web_service_is_stopped()

if __name__ == "__main__":
    unittest.main()
