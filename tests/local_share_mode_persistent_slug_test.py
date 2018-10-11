#!/usr/bin/env python3
import os
import sys
import unittest
import pytest
import json

from PyQt5 import QtWidgets

from onionshare.common import Common
from onionshare.web import Web
from onionshare import onion, strings
from onionshare_gui import *

from .GuiBaseTest import GuiBaseTest

class ShareModePersistentSlugTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "slug": "",
            "save_private_key": True,
            "close_after_first_download": False,
        }
        cls.gui = GuiBaseTest.set_up(test_settings, '/tmp/ShareModePersistentSlugTest.json')

    @classmethod
    def tearDownClass(cls):
        GuiBaseTest.tear_down()

    @pytest.mark.run(order=1000)
    def test_run_all_common_setup_tests(self):
        GuiBaseTest.run_all_common_setup_tests(self)

    @pytest.mark.run(order=1001)
    def test_run_all_persistent_share_mode_tests(self):
        GuiBaseTest.run_all_share_mode_tests(self, False, True)
        global slug
        slug = self.gui.share_mode.server_status.web.slug

    @pytest.mark.run(order=1002)
    def test_have_same_slug(self):
        '''Test that we have the same slug'''
        self.assertEqual(self.gui.share_mode.server_status.web.slug, slug)

if __name__ == "__main__":
    unittest.main()
