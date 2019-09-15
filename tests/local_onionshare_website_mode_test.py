#!/usr/bin/env python3
import pytest
import unittest

from .GuiWebsiteTest import GuiWebsiteTest

class LocalWebsiteModeTest(unittest.TestCase, GuiWebsiteTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = GuiWebsiteTest.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        GuiWebsiteTest.tear_down()

    @pytest.mark.gui
    @pytest.mark.skipif(pytest.__version__ < '2.9', reason="requires newer pytest")
    def test_gui(self):
        #self.run_all_common_setup_tests()
        self.run_all_website_mode_download_tests(False)

if __name__ == "__main__":
    unittest.main()
