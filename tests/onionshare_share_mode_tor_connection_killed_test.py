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

    @pytest.mark.tor
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(False)
        self.tor_killed_statusbar_message_shown(self.gui.share_mode)
        self.server_is_stopped(self.gui.share_mode, False)
        self.web_server_is_stopped()


if __name__ == "__main__":
    unittest.main()
