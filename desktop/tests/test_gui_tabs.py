import os

from PySide6 import QtCore, QtTest, QtWidgets

from .gui_base_test import GuiBaseTest


class TestTabs(GuiBaseTest):
    # Shared test methods

    def close_tab_with_active_server(self, tab):
        # Start the server
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_STOPPED,
        )
        tab.get_mode().server_status.server_button.click()
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_WORKING,
        )
        QtTest.QTest.qWait(1000, self.gui.qtapp)
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_STARTED,
        )

        # Prepare to reject the dialog
        QtCore.QTimer.singleShot(0, tab.close_dialog.reject_button.click)

        # Close tab
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()

        # The tab should still be open
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.get_mode().isVisible())

        # Prepare to accept the dialog
        QtCore.QTimer.singleShot(0, tab.close_dialog.accept_button.click)

        # Close tab
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()

        # The tab should be closed
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

    def close_persistent_tab(self, tab):
        # There shouldn't be a persistent settings file
        self.assertFalse(os.path.exists(tab.settings.filename))

        # Click the persistent checkbox
        tab.get_mode().server_status.mode_settings_widget.persistent_checkbox.click()
        QtTest.QTest.qWait(100, self.gui.qtapp)

        # There should be a persistent settings file now
        self.assertTrue(os.path.exists(tab.settings.filename))

        # Prepare to reject the dialog
        QtCore.QTimer.singleShot(0, tab.close_dialog.reject_button.click)

        # Close tab
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()

        # The tab should still be open
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.get_mode().isVisible())

        # There should be a persistent settings file still
        self.assertTrue(os.path.exists(tab.settings.filename))

        # Prepare to accept the dialog
        QtCore.QTimer.singleShot(0, tab.close_dialog.accept_button.click)

        # Close tab
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()

        # The tab should be closed
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

        # The persistent settings file should be deleted
        self.assertFalse(os.path.exists(tab.settings.filename))

    # Tests

    def test_01_common_tests(self):
        """Run all common tests"""
        self.run_all_common_setup_tests()

    def test_02_starts_with_one_new_tab(self):
        """There should be one "New Tab" tab open"""
        self.assertEqual(self.gui.tabs.count(), 1)
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

    def test_03_new_tab_button_opens_new_tabs(self):
        """Clicking the "+" button should open new tabs"""
        self.assertEqual(self.gui.tabs.count(), 1)
        self.gui.tabs.new_tab_button.click()
        self.gui.tabs.new_tab_button.click()
        self.gui.tabs.new_tab_button.click()
        self.assertEqual(self.gui.tabs.count(), 4)

    def test_04_close_tab_button_closes_tabs(self):
        """Clicking the "x" button should close tabs"""
        self.assertEqual(self.gui.tabs.count(), 4)
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()
        self.assertEqual(self.gui.tabs.count(), 1)

    def test_05_closing_last_tab_opens_new_one(self):
        """Closing the last tab should open a new tab"""
        self.assertEqual(self.gui.tabs.count(), 1)

        # Click share button
        self.gui.tabs.widget(0).share_button.click()
        self.assertFalse(self.gui.tabs.widget(0).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(0).share_mode.isVisible())

        # Close the tab
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()

        # A new tab should be opened
        self.assertEqual(self.gui.tabs.count(), 1)
        self.assertTrue(self.gui.tabs.widget(0).new_tab.isVisible())

    def test_06_new_tab_mode_buttons_show_correct_modes(self):
        """Clicking the mode buttons in a new tab should change the mode of the tab"""

        # New tab, share files
        self.gui.tabs.new_tab_button.click()
        self.gui.tabs.widget(1).share_button.click()
        self.assertFalse(self.gui.tabs.widget(1).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(1).share_mode.isVisible())
        self.assertEqual(
            self.gui.status_bar.server_status_label.text(), "Ready to share"
        )

        # New tab, receive files
        self.gui.tabs.new_tab_button.click()
        self.gui.tabs.widget(2).receive_button.click()
        self.assertFalse(self.gui.tabs.widget(2).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(2).receive_mode.isVisible())
        self.assertEqual(
            self.gui.status_bar.server_status_label.text(), "Ready to receive"
        )

        # New tab, publish website
        self.gui.tabs.new_tab_button.click()
        self.gui.tabs.widget(3).website_button.click()
        self.assertFalse(self.gui.tabs.widget(3).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(3).website_mode.isVisible())
        self.assertEqual(
            self.gui.status_bar.server_status_label.text(), "Ready to share"
        )

        # New tab, chat mode
        self.gui.tabs.new_tab_button.click()
        self.gui.tabs.widget(4).chat_button.click()
        self.assertFalse(self.gui.tabs.widget(4).new_tab.isVisible())
        self.assertTrue(self.gui.tabs.widget(4).chat_mode.isVisible())
        self.assertEqual(
            self.gui.status_bar.server_status_label.text(), "Ready to chat"
        )

        # Close tabs
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()
        self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()

    def test_07_close_share_tab_while_server_started_should_warn(self):
        """Closing a share mode tab when the server is running should throw a warning"""
        tab = self.new_share_tab_with_files()
        self.close_tab_with_active_server(tab)

    def test_08_close_receive_tab_while_server_started_should_warn(self):
        """Closing a receive mode tab when the server is running should throw a warning"""
        tab = self.new_receive_tab()
        self.close_tab_with_active_server(tab)

    def test_09_close_website_tab_while_server_started_should_warn(self):
        """Closing a website mode tab when the server is running should throw a warning"""
        tab = self.new_website_tab_with_files()
        self.close_tab_with_active_server(tab)

    def test_10_close_chat_tab_while_server_started_should_warn(self):
        """Closing a chat mode tab when the server is running should throw a warning"""
        tab = self.new_chat_tab()
        self.close_tab_with_active_server(tab)

    def test_11_close_persistent_share_tab_shows_warning(self):
        """Closing a share mode tab that's persistent should show a warning"""
        tab = self.new_share_tab_with_files()
        self.close_persistent_tab(tab)

    def test_12_close_persistent_receive_tab_shows_warning(self):
        """Closing a receive mode tab that's persistent should show a warning"""
        tab = self.new_receive_tab()
        self.close_persistent_tab(tab)

    def test_13_close_persistent_website_tab_shows_warning(self):
        """Closing a website mode tab that's persistent should show a warning"""
        tab = self.new_website_tab_with_files()
        self.close_persistent_tab(tab)

    def test_14_close_persistent_chat_tab_shows_warning(self):
        """Closing a chat mode tab that's persistent should show a warning"""
        tab = self.new_chat_tab()
        self.close_persistent_tab(tab)

    def test_15_quit_with_server_started_should_warn(self):
        """Quitting OnionShare with any active servers should show a warning"""
        tab = self.new_share_tab()

        # Start the server
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_STOPPED,
        )
        tab.get_mode().server_status.server_button.click()
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_WORKING,
        )
        QtTest.QTest.qWait(500, self.gui.qtapp)
        self.assertEqual(
            tab.get_mode().server_status.status,
            tab.get_mode().server_status.STATUS_STARTED,
        )

        # Prepare to reject the dialog
        QtCore.QTimer.singleShot(0, self.gui.close_dialog.reject_button.click)

        # Close the window
        self.gui.close()

        # The window should still be open
        self.assertTrue(self.gui.isVisible())

        # Stop the server
        tab.get_mode().server_status.server_button.click()
