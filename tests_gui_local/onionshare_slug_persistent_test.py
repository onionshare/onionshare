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
            "slug": "",
            "save_private_key": True
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
    def test_info_widget_is_visible(self):
        CommonTests.test_info_widget_is_visible(self, 'share')

    @pytest.mark.run(order=6)
    def test_history_is_visible(self):
        CommonTests.test_history_is_visible(self, 'share')

    @pytest.mark.run(order=7)
    def test_server_working_on_start_button_pressed(self):
        CommonTests.test_server_working_on_start_button_pressed(self, 'share')

    @pytest.mark.run(order=8)
    def test_server_status_indicator_says_starting(self):
        CommonTests.test_server_status_indicator_says_starting(self, 'share')

    @pytest.mark.run(order=9)
    def test_settings_button_is_hidden(self):
        CommonTests.test_settings_button_is_hidden(self)

    @pytest.mark.run(order=10)
    def test_a_server_is_started(self):
        CommonTests.test_a_server_is_started(self, 'share')

    @pytest.mark.run(order=11)
    def test_a_web_server_is_running(self):
        CommonTests.test_a_web_server_is_running(self)

    @pytest.mark.run(order=12)
    def test_have_a_slug(self):
        CommonTests.test_have_a_slug(self, 'share', False)
        global slug
        slug = self.gui.share_mode.server_status.web.slug

    @pytest.mark.run(order=13)
    def test_server_status_indicator_says_started(self):
        CommonTests.test_server_status_indicator_says_started(self, 'share')

    @pytest.mark.run(order=14)
    def test_server_is_stopped(self):
        CommonTests.test_server_is_stopped(self, 'share', True)

    @pytest.mark.run(order=15)
    def test_web_service_is_stopped(self):
        CommonTests.test_web_service_is_stopped(self)

    @pytest.mark.run(order=16)
    def test_server_status_indicator_says_closed(self):
        CommonTests.test_server_status_indicator_says_closed(self, 'share', True)

    @pytest.mark.run(order=17)
    def test_server_started_again(self):
        CommonTests.test_server_working_on_start_button_pressed(self, 'share')
        CommonTests.test_server_status_indicator_says_starting(self, 'share')
        CommonTests.test_a_server_is_started(self, 'share')

    @pytest.mark.run(order=18)
    def test_have_same_slug(self):
        '''Test that we have the same slug'''
        self.assertEqual(self.gui.share_mode.server_status.web.slug, slug)

    @pytest.mark.run(order=19)
    def test_server_is_stopped_again(self):
        CommonTests.test_server_is_stopped(self, 'share', True)
        CommonTests.test_web_service_is_stopped(self)


if __name__ == "__main__":
    unittest.main()
