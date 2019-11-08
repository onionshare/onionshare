import pytest
import os

from PyQt5 import QtCore, QtTest, QtWidgets

from .gui_base_test import GuiBaseTest


class TestTabs(GuiBaseTest):
    # Shared test methods

    def verify_new_tab(self, tab):
        # Make sure the new tab widget is showing, and no mode has been started
        self.assertTrue(tab.new_tab.isVisible())
        self.assertFalse(hasattr(tab, "share_mode"))
        self.assertFalse(hasattr(tab, "receive_mode"))
        self.assertFalse(hasattr(tab, "website_mode"))

    def new_share_tab(self):
        tab = self.gui.tabs.widget(0)
        self.verify_new_tab(tab)

        # Share files
        QtTest.QTest.mouseClick(tab.share_button, QtCore.Qt.LeftButton)
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.share_mode.isVisible())

        # Add files
        for filename in self.tmpfiles:
            tab.share_mode.server_status.file_selection.file_list.add_file(filename)

        return tab

    def new_receive_tab(self):
        tab = self.gui.tabs.widget(0)
        self.verify_new_tab(tab)

        # Receive files
        QtTest.QTest.mouseClick(tab.receive_button, QtCore.Qt.LeftButton)
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.receive_mode.isVisible())

        return tab

    def new_website_tab(self):
        tab = self.gui.tabs.widget(0)
        self.verify_new_tab(tab)

        # Publish website
        QtTest.QTest.mouseClick(tab.website_button, QtCore.Qt.LeftButton)
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.website_mode.isVisible())

        # Add files
        for filename in self.tmpfiles:
            tab.website_mode.server_status.file_selection.file_list.add_file(filename)

        return tab

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

        # The tab should be closed
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

    def close_persistent_tab(self, tab):
        # There shouldn't be a persistent settings file
        self.assertFalse(os.path.exists(tab.settings.filename))

        # Click the persistent checkbox
        tab.get_mode().server_status.mode_settings_widget.persistent_checkbox.click()
        QtTest.QTest.qWait(100)

        # There should be a persistent settings file now
        self.assertTrue(os.path.exists(tab.settings.filename))

        # Prepare to reject the dialog
        QtCore.QTimer.singleShot(1000, tab.close_dialog.reject_button.click)

        # Close tab
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )

        # The tab should still be open
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.get_mode().isVisible())

        # There should be a persistent settings file still
        self.assertTrue(os.path.exists(tab.settings.filename))

        # Prepare to accept the dialog
        QtCore.QTimer.singleShot(1000, tab.close_dialog.accept_button.click)

        # Close tab
        QtTest.QTest.mouseClick(
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide),
            QtCore.Qt.LeftButton,
        )

        # The tab should be closed
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

        # The persistent settings file should be deleted
        self.assertFalse(os.path.exists(tab.settings.filename))

    # Tests

    @pytest.mark.gui
    def test_01_common_tests(self):
        """Run all common tests"""
        self.run_all_common_setup_tests()

    @pytest.mark.gui
    def test_02_starts_with_one_new_tab(self):
        """There should be one "New Tab" tab open"""
        self.assertEqual(self.gui.tabs.count(), 1)
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

    @pytest.mark.gui
    def test_03_new_tab_button_opens_new_tabs(self):
        """Clicking the "+" button should open new tabs"""
        self.assertEqual(self.gui.tabs.count(), 1)
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.gui.tabs.new_tab_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.tabs.count(), 4)

    @pytest.mark.gui
    def test_04_close_tab_button_closes_tabs(self):
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
    def test_05_closing_last_tab_opens_new_one(self):
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
    def test_06_new_tab_mode_buttons_show_correct_modes(self):
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
    def test_07_close_share_tab_while_server_started_should_warn(self):
        """Closing a share mode tab when the server is running should throw a warning"""
        tab = self.new_share_tab()
        self.close_tab_with_active_server(tab)

    @pytest.mark.gui
    def test_08_close_receive_tab_while_server_started_should_warn(self):
        """Closing a recieve mode tab when the server is running should throw a warning"""
        tab = self.new_receive_tab()
        self.close_tab_with_active_server(tab)

    @pytest.mark.gui
    def test_09_close_website_tab_while_server_started_should_warn(self):
        """Closing a website mode tab when the server is running should throw a warning"""
        tab = self.new_website_tab()
        self.close_tab_with_active_server(tab)

    @pytest.mark.gui
    def test_10_close_persistent_share_tab_shows_warning(self):
        """Closing a share mode tab that's persistent should show a warning"""
        tab = self.new_share_tab()
        self.close_persistent_tab(tab)

    @pytest.mark.gui
    def test_11_close_persistent_receive_tab_shows_warning(self):
        """Closing a receive mode tab that's persistent should show a warning"""
        tab = self.new_receive_tab()
        self.close_persistent_tab(tab)

    @pytest.mark.gui
    def test_12_close_persistent_website_tab_shows_warning(self):
        """Closing a website mode tab that's persistent should show a warning"""
        tab = self.new_website_tab()
        self.close_persistent_tab(tab)

    @pytest.mark.gui
    def test_13_quit_with_server_started_should_warn(self):
        """Quitting OnionShare with any active servers should show a warning"""
        tab = self.new_share_tab()

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
        QtCore.QTimer.singleShot(1000, self.gui.close_dialog.reject_button.click)

        # Close the window
        self.gui.close()

        # The window should still be open
        self.assertTrue(self.gui.isVisible())

        # Stop the server
        QtTest.QTest.mouseClick(
            tab.get_mode().server_status.server_button, QtCore.Qt.LeftButton
        )
