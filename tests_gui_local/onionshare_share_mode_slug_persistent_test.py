#!/usr/bin/env python3
import pytest
import unittest

from .GuiShareTest import GuiShareTest

class ShareModePersistentSlugTest(unittest.TestCase, GuiShareTest):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "slug": "",
            "save_private_key": True,
            "close_after_first_download": False,
        }
        cls.gui = GuiShareTest.set_up(test_settings, 'ShareModePersistentSlugTest')

    @classmethod
    def tearDownClass(cls):
        GuiShareTest.tear_down()

    @pytest.mark.run(order=1)
    def test_run_all_common_setup_tests(self):
        GuiShareTest.run_all_common_setup_tests(self)

    @pytest.mark.run(order=2)
    def test_run_all_share_mode_tests(self):
        GuiShareTest.run_all_share_mode_tests(self, False, True)
        global slug
        slug = self.gui.share_mode.server_status.web.slug

    @pytest.mark.run(order=3)
    def test_have_same_slug(self):
        '''Test that we have the same slug'''
        self.assertEqual(self.gui.share_mode.server_status.web.slug, slug)

if __name__ == "__main__":
    unittest.main()
