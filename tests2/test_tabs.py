#!/usr/bin/env python3
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


class TestTabs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        common = Common()
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
        cls.gui.cleanup()

    def close_tab_with_active_server(self, tab):
        # Start the server
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_STOPPED,
        )
        QtTest.QTest.mouseClick(
            tab.get_mode().server_status.server_button, QtCore.Qt.LeftButton
        )
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_WORKING,
        )
        QtTest.QTest.qWait(1000)
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_STARTED,
        )

        # Prepare to reject the dialog
        QtCore.QTimer.singleShot(1000, tab.close_dialog.reject_button.click)

        # Close tab
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )
        QtTest.QTest.qWait(1000)

        # The tab should still be open
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.get_mode().isVisible())

        # Prepare to accept the dialog
        QtCore.QTimer.singleShot(1000, tab.close_dialog.accept_button.click)

        # Close tab
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )
        QtTest.QTest.qWait(1000)

        # The tab should be closed
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

    @pytest.mark.gui
    def test_001_gui_loaded(self):
        """Test that the GUI actually is shown"""
        self.assertTrue(self.gui.show)

    @pytest.mark.gui
    def test_002_window_title_seen(self):
        """Test that the window title is OnionShare"""
        self.assertEqual(self.gui.windowTitle(), "OnionShare")

    @pytest.mark.gui
    def test_003_settings_button_is_visible(self):
        """Test that the settings button is visible"""
        self.assertTrue(self.gui.settings_button.isVisible())

    @pytest.mark.gui
    def test_004_server_status_bar_is_visible(self):
        """Test that the status bar is visible"""
        self.assertTrue(self.gui.status_bar.isVisible())

    @pytest.mark.gui
    def test_005_starts_with_one_new_tab(self):
        """There should be one "New Tab" tab open"""
        self.assertEqual(self.gui.tabs.count(), 1)
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

    @pytest.mark.gui
    def test_006_new_tab_button_opens_new_tabs(self):
        """Clicking the "+" button should open new tabs"""
        self.assertEqual(self.gui.tabs.count(), 1)
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.tabs.count(), 4)

    @pytest.mark.gui
    def test_007_close_tab_button_closes_tabs(self):
        """Clicking the "x" button should close tabs"""
        self.assertEqual(self.gui.tabs.count(), 4)
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )
        self.assertEqual(self.gui.tabs.count(), 1)

    @pytest.mark.gui
    def test_008_closing_last_tab_opens_new_one(self):
        """Closing the last tab should open a new tab"""
        self.assertEqual(self.gui.tabs.count(), 1)

        # Click share button
        QtTest.QTest.mouseClick(
            self.gui.tabs.widget(0).share_button, QtCore.Qt.LeftButton
        )
        self.assertFalse(self.gui.tabs.widget(0).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(0).share_mode.isVisible())

        # Close the tab
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )

        # A new tab should be opened
        self.assertEqual(self.gui.tabs.count(), 1)
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

    @pytest.mark.gui
    def test_009_new_tab_mode_buttons_show_correct_modes(self):
        """Clicking the mode buttons in a new tab should change the mode of the tab"""

        # New tab, share files
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(
            self.gui.tabs.widget(1).share_button, QtCore.Qt.LeftButton
        )
        self.assertFalse(self.gui.tabs.widget(1).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(1).share_mode.isVisible())

        # New tab, receive files
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(
            self.gui.tabs.widget(2).receive_button, QtCore.Qt.LeftButton
        )
        self.assertFalse(self.gui.tabs.widget(2).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(2).receive_mode.isVisible())

        # New tab, publish website
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(
            self.gui.tabs.widget(3).website_button, QtCore.Qt.LeftButton
        )
        self.assertFalse(self.gui.tabs.widget(3).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(3).website_mode.isVisible())

        # Close tabs
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )

    @pytest.mark.gui
    def test_010_close_share_tab_while_server_started_should_warn(self):
        """Closing a share mode tab when the server is running should throw a warning"""
        tab = self.gui.tabs.widget(0)

        # Share files
        QtTest.QTest.mouseClick(tab.share_button, QtCore.Qt.LeftButton)
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.share_mode.isVisible())

        # Add files
        for filename in self.tmpfiles:
            tab.share_mode.server_status.file_selection.file_list.add_file(filename)

        # Test closing it
        self.close_tab_with_active_server(tab)

    @pytest.mark.gui
    def test_011_close_receive_tab_while_server_started_should_warn(self):
        """Closing a recieve mode tab when the server is running should throw a warning"""
        tab = self.gui.tabs.widget(0)

        # Receive files
        QtTest.QTest.mouseClick(tab.receive_button, QtCore.Qt.LeftButton)
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.receive_mode.isVisible())

        # Test closing it
        self.close_tab_with_active_server(tab)

    @pytest.mark.gui
    def test_012_close_website_tab_while_server_started_should_warn(self):
        """Closing a website mode tab when the server is running should throw a warning"""
        tab = self.gui.tabs.widget(0)

        # Publish website
        QtTest.QTest.mouseClick(tab.website_button, QtCore.Qt.LeftButton)
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.website_mode.isVisible())

        # Add files
        for filename in self.tmpfiles:
            tab.website_mode.server_status.file_selection.file_list.add_file(filename)

        # Test closing it
        self.close_tab_with_active_server(tab)


if __name__ == "__main__":
    unittest.main()
