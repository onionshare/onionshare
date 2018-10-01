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

from .commontests import CommonTests

class OnionShareGuiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_settings = {
            "public_mode": False,
            "shutdown_timeout": True
        }
        cls.gui = CommonTests.set_up(test_settings)

    @classmethod
    def tearDownClass(cls):
        CommonTests.tear_down()

    @pytest.mark.run(order=1)
    def test_gui_loaded(self):
        CommonTests.test_gui_loaded(self)

    @pytest.mark.run(order=2)
    def test_windowTitle_seen(self):
        CommonTests.test_windowTitle_seen(self)

    @pytest.mark.run(order=3)
    def test_settings_button_is_visible(self):
        CommonTests.test_settings_button_is_visible(self)

    @pytest.mark.run(order=4)
    def test_server_status_bar_is_visible(self):
        CommonTests.test_server_status_bar_is_visible(self)

    @pytest.mark.run(order=5)
    def test_file_selection_widget_has_a_file(self):
        CommonTests.test_file_selection_widget_has_a_file(self)

    @pytest.mark.run(order=6)
    def test_info_widget_is_visible(self):
        CommonTests.test_info_widget_is_visible(self, 'share')

    @pytest.mark.run(order=7)
    def test_history_is_visible(self):
        CommonTests.test_history_is_visible(self, 'share')

    @pytest.mark.run(order=8)
    def test_set_timeout(self):
        CommonTests.test_set_timeout(self, 'share', 5)

    @pytest.mark.run(order=9)
    def test_server_working_on_start_button_pressed(self):
        CommonTests.test_server_working_on_start_button_pressed(self, 'share')

    @pytest.mark.run(order=10)
    def test_server_status_indicator_says_starting(self):
        CommonTests.test_server_status_indicator_says_starting(self, 'share')

    @pytest.mark.run(order=11)
    def test_a_server_is_started(self):
       CommonTests.test_a_server_is_started(self, 'share')

    @pytest.mark.run(order=12)
    def test_a_web_server_is_running(self):
        CommonTests.test_a_web_server_is_running(self)

    @pytest.mark.run(order=13)
    def test_timeout_widget_hidden(self):
        CommonTests.test_timeout_widget_hidden(self, 'share')

    @pytest.mark.run(order=14)
    def test_timeout(self):
        CommonTests.test_server_timed_out(self, 'share', 10000)

    @pytest.mark.run(order=15)
    def test_web_service_is_stopped(self):
        CommonTests.test_web_service_is_stopped(self)

if __name__ == "__main__":
    unittest.main()
