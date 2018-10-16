#!/usr/bin/env python3
import unittest

from .GuiShareTest import GuiShareTest

class LocalShareModeTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = GuiShareTest.set_up(test_settings, 'LocalShareModeTest')

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    def test_gui(self):
        self.run_all_common_setup_tests()
        self.run_all_large_file_tests(False, True)

if __name__ == "__main__":
    unittest.main()
