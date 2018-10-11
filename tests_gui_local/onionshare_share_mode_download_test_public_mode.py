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
            "public_mode": True
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

    @pytest.mark.run(order=7)
    def test_history_is_not_visible(self):
        CommonTests.test_history_is_not_visible(self, self.gui.share_mode)

    @pytest.mark.run(order=8)
    def test_click_toggle_history(self):
        CommonTests.test_click_toggle_history(self, self.gui.share_mode)

    @pytest.mark.run(order=9)
    def test_history_is_visible(self):
        CommonTests.test_history_is_visible(self, self.gui.share_mode)

    @pytest.mark.run(order=10)
    def test_deleting_only_file_hides_delete_button(self):
        CommonTests.test_deleting_only_file_hides_delete_button(self)

    @pytest.mark.run(order=11)
    def test_add_a_file_and_delete_using_its_delete_widget(self):
        CommonTests.test_add_a_file_and_delete_using_its_delete_widget(self)

    @pytest.mark.run(order=12)
    def test_file_selection_widget_readd_files(self):
        CommonTests.test_file_selection_widget_readd_files(self)

    @pytest.mark.run(order=13)
    def test_server_working_on_start_button_pressed(self):
        CommonTests.test_server_working_on_start_button_pressed(self, self.gui.share_mode)

    @pytest.mark.run(order=14)
    def test_server_status_indicator_says_starting(self):
        CommonTests.test_server_status_indicator_says_starting(self, self.gui.share_mode)

    @pytest.mark.run(order=15)
    def test_add_delete_buttons_hidden(self):
        CommonTests.test_add_delete_buttons_hidden(self)

    @pytest.mark.run(order=16)
    def test_settings_button_is_hidden(self):
        CommonTests.test_settings_button_is_hidden(self)

    @pytest.mark.run(order=17)
    def test_a_server_is_started(self):
       CommonTests.test_a_server_is_started(self, self.gui.share_mode)

    @pytest.mark.run(order=18)
    def test_a_web_server_is_running(self):
        CommonTests.test_a_web_server_is_running(self)

    @pytest.mark.run(order=19)
    def test_have_a_slug(self):
        CommonTests.test_have_a_slug(self, self.gui.share_mode, True)

    @pytest.mark.run(order=20)
    def test_url_description_shown(self):
        CommonTests.test_url_description_shown(self, self.gui.share_mode)

    @pytest.mark.run(order=21)
    def test_have_copy_url_button(self):
        CommonTests.test_have_copy_url_button(self, self.gui.share_mode)

    @pytest.mark.run(order=22)
    def test_server_status_indicator_says_started(self):
        CommonTests.test_server_status_indicator_says_started(self, self.gui.share_mode)

    @pytest.mark.run(order=23)
    def test_web_page(self):
        CommonTests.test_web_page(self, self.gui.share_mode, 'Total size', True)

    @pytest.mark.run(order=24)
    def test_download_share(self):
        CommonTests.test_download_share(self, True)

    @pytest.mark.run(order=25)
    def test_history_widgets_present(self):
        CommonTests.test_history_widgets_present(self, self.gui.share_mode)

    @pytest.mark.run(order=26)
    def test_server_is_stopped(self):
        CommonTests.test_server_is_stopped(self, self.gui.share_mode, False)

    @pytest.mark.run(order=27)
    def test_web_service_is_stopped(self):
        CommonTests.test_web_service_is_stopped(self)

    @pytest.mark.run(order=28)
    def test_server_status_indicator_says_closed(self):
        CommonTests.test_server_status_indicator_says_closed(self, self.gui.share_mode, False)

    @pytest.mark.run(order=29)
    def test_add_button_visible(self):
        CommonTests.test_add_button_visible(self)

    @pytest.mark.run(order=30)
    def test_history_indicator(self):
        CommonTests.test_server_working_on_start_button_pressed(self, self.gui.share_mode)
        CommonTests.test_a_server_is_started(self, self.gui.share_mode)
        CommonTests.test_history_indicator(self, self.gui.share_mode, True)


if __name__ == "__main__":
    unittest.main()
