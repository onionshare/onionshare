import pytest
import unittest

import json
import os
import requests
import shutil
import base64
import tempfile
import secrets

from PyQt5 import QtCore, QtTest, QtWidgets

from onionshare import strings
from onionshare.common import Common
from onionshare.settings import Settings
from onionshare.onion import Onion
from onionshare.web import Web

from onionshare_gui import Application, MainWindow, GuiCommon
from onionshare_gui.tab.mode.share_mode import ShareMode
from onionshare_gui.tab.mode.receive_mode import ReceiveMode
from onionshare_gui.tab.mode.website_mode import WebsiteMode


class GuiBaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        common = Common(verbose=True)
        qtapp = Application(common)
        common.gui = GuiCommon(common, qtapp, local_only=True)
        cls.gui = MainWindow(common, filenames=None)
        cls.gui.qtapp = qtapp

        # Create some random files to test with
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.tmpfiles = []
        for _ in range(10):
            filename = os.path.join(cls.tmpdir.name, f"{secrets.token_hex(4)}.txt")
            with open(filename, "w") as file:
                file.write(secrets.token_hex(10))
            cls.tmpfiles.append(filename)

    @classmethod
    def tearDownClass(cls):
        cls.gui.close()
        cls.gui.cleanup()

    # Shared test methods

    def gui_loaded(self):
        """Test that the GUI actually is shown"""
        self.assertTrue(self.gui.show)

    def window_title_seen(self):
        """Test that the window title is OnionShare"""
        self.assertEqual(self.gui.windowTitle(), "OnionShare")

    def settings_button_is_visible(self):
        """Test that the settings button is visible"""
        self.assertTrue(self.gui.settings_button.isVisible())

    def settings_button_is_hidden(self):
        """Test that the settings button is hidden when the server starts"""
        self.assertFalse(self.gui.settings_button.isVisible())

    def server_status_bar_is_visible(self):
        """Test that the status bar is visible"""
        self.assertTrue(self.gui.status_bar.isVisible())

    def click_mode(self, mode):
        """Test that we can switch Mode by clicking the button"""
        if type(mode) == ReceiveMode:
            QtTest.QTest.mouseClick(self.gui.receive_mode_button, QtCore.Qt.LeftButton)
            self.assertTrue(self.gui.mode, self.gui.MODE_RECEIVE)
        if type(mode) == ShareMode:
            QtTest.QTest.mouseClick(self.gui.share_mode_button, QtCore.Qt.LeftButton)
            self.assertTrue(self.gui.mode, self.gui.MODE_SHARE)
        if type(mode) == WebsiteMode:
            QtTest.QTest.mouseClick(self.gui.website_mode_button, QtCore.Qt.LeftButton)
            self.assertTrue(self.gui.mode, self.gui.MODE_WEBSITE)

    def click_toggle_history(self, mode):
        """Test that we can toggle Download or Upload history by clicking the toggle button"""
        currently_visible = mode.history.isVisible()
        QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
        self.assertEqual(mode.history.isVisible(), not currently_visible)

    def history_indicator(self, mode, public_mode, indicator_count="1"):
        """Test that we can make sure the history is toggled off, do an action, and the indiciator works"""
        # Make sure history is toggled off
        if mode.history.isVisible():
            QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
            self.assertFalse(mode.history.isVisible())

        # Indicator should not be visible yet
        self.assertFalse(mode.toggle_history.indicator_label.isVisible())

        if type(mode) == ReceiveMode:
            # Upload a file
            files = {"file[]": open("/tmp/test.txt", "rb")}
            url = f"http://127.0.0.1:{self.gui.app.port}/upload"
            if public_mode:
                requests.post(url, files=files)
            else:
                requests.post(
                    url,
                    files=files,
                    auth=requests.auth.HTTPBasicAuth("onionshare", mode.web.password),
                )
            QtTest.QTest.qWait(2000)

        if type(mode) == ShareMode:
            # Download files
            url = f"http://127.0.0.1:{self.gui.app.port}/download"
            if public_mode:
                requests.get(url)
            else:
                requests.get(
                    url,
                    auth=requests.auth.HTTPBasicAuth("onionshare", mode.web.password),
                )
            QtTest.QTest.qWait(2000)

        # Indicator should be visible, have a value of "1"
        self.assertTrue(mode.toggle_history.indicator_label.isVisible())
        self.assertEqual(mode.toggle_history.indicator_label.text(), indicator_count)

        # Toggle history back on, indicator should be hidden again
        QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
        self.assertFalse(mode.toggle_history.indicator_label.isVisible())

    def history_is_not_visible(self, mode):
        """Test that the History section is not visible"""
        self.assertFalse(mode.history.isVisible())

    def history_is_visible(self, mode):
        """Test that the History section is visible"""
        self.assertTrue(mode.history.isVisible())

    def server_working_on_start_button_pressed(self, mode):
        """Test we can start the service"""
        # Should be in SERVER_WORKING state
        QtTest.QTest.mouseClick(mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(mode.server_status.status, 1)

    def toggle_indicator_is_reset(self, mode):
        self.assertEqual(mode.toggle_history.indicator_count, 0)
        self.assertFalse(mode.toggle_history.indicator_label.isVisible())

    def server_status_indicator_says_starting(self, mode):
        """Test that the Server Status indicator shows we are Starting"""
        self.assertEqual(
            mode.server_status_label.text(),
            strings._("gui_status_indicator_share_working"),
        )

    def server_status_indicator_says_scheduled(self, mode):
        """Test that the Server Status indicator shows we are Scheduled"""
        self.assertEqual(
            mode.server_status_label.text(),
            strings._("gui_status_indicator_share_scheduled"),
        )

    def server_is_started(self, mode, startup_time=2000):
        """Test that the server has started"""
        QtTest.QTest.qWait(startup_time)
        # Should now be in SERVER_STARTED state
        self.assertEqual(mode.server_status.status, 2)

    def web_server_is_running(self):
        """Test that the web server has started"""
        try:
            r = requests.get(f"http://127.0.0.1:{self.gui.app.port}/")
            self.assertTrue(True)
        except requests.exceptions.ConnectionError:
            self.assertTrue(False)

    def have_a_password(self, mode, public_mode):
        """Test that we have a valid password"""
        if not public_mode:
            self.assertRegex(mode.server_status.web.password, r"(\w+)-(\w+)")
        else:
            self.assertIsNone(mode.server_status.web.password, r"(\w+)-(\w+)")

    def add_button_visible(self, mode):
        """Test that the add button should be visible"""
        self.assertTrue(mode.server_status.file_selection.add_button.isVisible())

    def url_description_shown(self, mode):
        """Test that the URL label is showing"""
        self.assertTrue(mode.server_status.url_description.isVisible())

    def have_copy_url_button(self, mode, public_mode):
        """Test that the Copy URL button is shown and that the clipboard is correct"""
        self.assertTrue(mode.server_status.copy_url_button.isVisible())

        QtTest.QTest.mouseClick(
            mode.server_status.copy_url_button, QtCore.Qt.LeftButton
        )
        clipboard = self.gui.qtapp.clipboard()
        if public_mode:
            self.assertEqual(clipboard.text(), f"http://127.0.0.1:{self.gui.app.port}")
        else:
            self.assertEqual(
                clipboard.text(),
                f"http://onionshare:{mode.server_status.web.password}@127.0.0.1:{self.gui.app.port}",
            )

    def server_status_indicator_says_started(self, mode):
        """Test that the Server Status indicator shows we are started"""
        if type(mode) == ReceiveMode:
            self.assertEqual(
                mode.server_status_label.text(),
                strings._("gui_status_indicator_receive_started"),
            )
        if type(mode) == ShareMode:
            self.assertEqual(
                mode.server_status_label.text(),
                strings._("gui_status_indicator_share_started"),
            )

    def web_page(self, mode, string, public_mode):
        """Test that the web page contains a string"""

        url = f"http://127.0.0.1:{self.gui.app.port}/"
        if public_mode:
            r = requests.get(url)
        else:
            r = requests.get(
                url, auth=requests.auth.HTTPBasicAuth("onionshare", mode.web.password)
            )

        self.assertTrue(string in r.text)

    def history_widgets_present(self, mode):
        """Test that the relevant widgets are present in the history view after activity has taken place"""
        self.assertFalse(mode.history.empty.isVisible())
        self.assertTrue(mode.history.not_empty.isVisible())

    def counter_incremented(self, mode, count):
        """Test that the counter has incremented"""
        self.assertEqual(mode.history.completed_count, count)

    def server_is_stopped(self, mode, stay_open):
        """Test that the server stops when we click Stop"""
        if (
            type(mode) == ReceiveMode
            or (type(mode) == ShareMode and stay_open)
            or (type(mode) == WebsiteMode)
        ):
            QtTest.QTest.mouseClick(
                mode.server_status.server_button, QtCore.Qt.LeftButton
            )
        self.assertEqual(mode.server_status.status, 0)

    def web_server_is_stopped(self):
        """Test that the web server also stopped"""
        QtTest.QTest.qWait(2000)

        try:
            r = requests.get(f"http://127.0.0.1:{self.gui.app.port}/")
            self.assertTrue(False)
        except requests.exceptions.ConnectionError:
            self.assertTrue(True)

    def server_status_indicator_says_closed(self, mode, stay_open):
        """Test that the Server Status indicator shows we closed"""
        if type(mode) == ReceiveMode:
            self.assertEqual(
                self.gui.receive_mode.server_status_label.text(),
                strings._("gui_status_indicator_receive_stopped"),
            )
        if type(mode) == ShareMode:
            if stay_open:
                self.assertEqual(
                    self.gui.share_mode.server_status_label.text(),
                    strings._("gui_status_indicator_share_stopped"),
                )
            else:
                self.assertEqual(
                    self.gui.share_mode.server_status_label.text(),
                    strings._("closing_automatically"),
                )

    def clear_all_history_items(self, mode, count):
        if count == 0:
            QtTest.QTest.mouseClick(mode.history.clear_button, QtCore.Qt.LeftButton)
        self.assertEquals(len(mode.history.item_list.items.keys()), count)

    # Auto-stop timer tests
    def set_timeout(self, mode, timeout):
        """Test that the timeout can be set"""
        timer = QtCore.QDateTime.currentDateTime().addSecs(timeout)
        mode.server_status.autostop_timer_widget.setDateTime(timer)
        self.assertTrue(mode.server_status.autostop_timer_widget.dateTime(), timer)

    def autostop_timer_widget_hidden(self, mode):
        """Test that the auto-stop timer widget is hidden when share has started"""
        self.assertFalse(mode.server_status.autostop_timer_container.isVisible())

    def server_timed_out(self, mode, wait):
        """Test that the server has timed out after the timer ran out"""
        QtTest.QTest.qWait(wait)
        # We should have timed out now
        self.assertEqual(mode.server_status.status, 0)

    # Hack to close an Alert dialog that would otherwise block tests
    def accept_dialog(self):
        window = self.gui.qtapp.activeWindow()
        if window:
            window.close()

    # Grouped tests follow from here

    def run_all_common_setup_tests(self):
        self.gui_loaded()
        self.window_title_seen()
        self.settings_button_is_visible()
        self.server_status_bar_is_visible()
