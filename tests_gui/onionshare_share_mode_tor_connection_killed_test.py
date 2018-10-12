#!/usr/bin/env python3
import pytest
import unittest

from .TorGuiShareTest import TorGuiShareTest

class ShareModeTorConnectionKilledTest(unittest.TestCase, TorGuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = TorGuiShareTest.set_up(test_settings, 'ShareModeTorConnectionKilledTest')

    @pytest.mark.run(order=1)
    @pytest.mark.tor
    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(order=2)
    @pytest.mark.tor
    def test_run_share_mode_setup_tests(self):
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(False)

    @pytest.mark.run(order=3)
    @pytest.mark.tor
    def test_tor_killed_statusbar_message_shown(self):
        self.tor_killed_statusbar_message_shown(self.gui.share_mode)

    @pytest.mark.run(order=4)
    @pytest.mark.tor
    def test_server_is_stopped(self):
        self.server_is_stopped(self.gui.share_mode, False)

    @pytest.mark.run(order=5)
    @pytest.mark.tor
    def test_web_service_is_stopped(self):
        self.web_service_is_stopped()


if __name__ == "__main__":
    unittest.main()
