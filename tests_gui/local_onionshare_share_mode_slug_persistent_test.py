#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModePersistentSlugTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "slug": "",
            "save_private_key": True,
            "close_after_first_download": False,
        }
        cls.gui = GuiShareTest.set_up(test_settings, 'LocalShareModePersistentSlugTest')

    @pytest.mark.run(order=1)
    def test_run_all_common_setup_tests(self):
        self.run_all_common_setup_tests()

    @pytest.mark.run(order=2)
    def test_run_all_share_mode_tests(self):
        self.run_all_share_mode_persistent_tests(False, True)

if __name__ == "__main__":
    unittest.main()
