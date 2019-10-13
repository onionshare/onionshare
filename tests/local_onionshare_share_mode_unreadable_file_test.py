#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest


class LocalShareModeUnReadableFileTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {}
        cls.gui = GuiShareTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    @pytest.mark.gui
    @pytest.mark.skipif(pytest.__version__ < "2.9", reason="requires newer pytest")
    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_share_mode_unreadable_file_tests()


if __name__ == "__main__":
    unittest.main()
