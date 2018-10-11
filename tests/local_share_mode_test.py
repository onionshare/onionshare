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

class ShareModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_settings = {
        }
        cls.gui = GuiBaseTest.set_up(test_settings, '/tmp/ShareModeTest.json')

    @classmethod
    def tearDownClass(cls):
        GuiBaseTest.tear_down()

    @pytest.mark.run(order=1)
    def test_run_all_common_setup_tests(self):
        GuiBaseTest.run_all_common_setup_tests(self)

    @pytest.mark.run(order=2)
    def test_run_all_share_mode_tests(self):
        GuiBaseTest.run_all_share_mode_tests(self, False, False)

if __name__ == "__main__":
    unittest.main()
