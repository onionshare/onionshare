import unittest
import os
import requests
import shutil
import tempfile
import secrets
import platform
import sys

from PySide2 import QtCore, QtTest, QtWidgets

from onionshare_cli.common import Common

from onionshare import Application, MainWindow, GuiCommon
from onionshare.tab.mode.share_mode import ShareMode
from onionshare.tab.mode.receive_mode import ReceiveMode
from onionshare.tab.mode.website_mode import WebsiteMode
from onionshare.tab.mode.chat_mode import ChatMode
from onionshare import strings


class GuiBaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        common = sys.onionshare_common
        qtapp = sys.onionshare_qtapp

        # Delete any old test data that might exist
        shutil.rmtree(common.build_data_dir(), ignore_errors=True)

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

        # A file called "test.txt"
        cls.tmpfile_test = os.path.join(cls.tmpdir.name, "test.txt")
        with open(cls.tmpfile_test, "w") as file:
            file.write("onionshare")

        # A file called "test2.txt"
        cls.tmpfile_test2 = os.path.join(cls.tmpdir.name, "test2.txt")
        with open(cls.tmpfile_test2, "w") as file:
            file.write("onionshare2")

        # A file called "index.html"
        cls.tmpfile_index_html = os.path.join(cls.tmpdir.name, "index.html")
        with open(cls.tmpfile_index_html, "w") as file:
            file.write(
                "<html><body><p>This is a test website hosted by OnionShare</p></body></html>"
            )

        # A large file
        size = 1024 * 1024 * 155
        cls.tmpfile_large = os.path.join(cls.tmpdir.name, "large_file")
        with open(cls.tmpfile_large, "wb") as fout:
            fout.write(os.urandom(size))

    @classmethod
    def tearDownClass(cls):
        # Quit
        cls.gui.qtapp.clipboard().clear()
        QtCore.QTimer.singleShot(200, cls.gui.close_dialog.accept_button.click)
        cls.gui.close()

        cls.gui.cleanup()

    # Shared test methods

    def verify_new_tab(self, tab):
        # Make sure the new tab widget is showing, and no mode has been started
        QtTest.QTest.qWait(1000, self.gui.qtapp)
        self.assertTrue(tab.new_tab.isVisible())
        self.assertFalse(hasattr(tab, "share_mode"))
        self.assertFalse(hasattr(tab, "receive_mode"))
        self.assertFalse(hasattr(tab, "website_mode"))
        self.assertFalse(hasattr(tab, "chat_mode"))

    def new_share_tab(self):
        tab = self.gui.tabs.widget(0)
        self.verify_new_tab(tab)

        # Share files
        tab.share_button.click()
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.share_mode.isVisible())

        return tab

    def new_share_tab_with_files(self):
        tab = self.new_share_tab()

        # Add files
        for filename in self.tmpfiles:
            tab.share_mode.server_status.file_selection.file_list.add_file(filename)

        return tab

    def new_receive_tab(self):
        tab = self.gui.tabs.widget(0)
        self.verify_new_tab(tab)

        # Receive files
        tab.receive_button.click()
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.receive_mode.isVisible())

        return tab

    def new_website_tab(self):
        tab = self.gui.tabs.widget(0)
        self.verify_new_tab(tab)

        # Publish website
        tab.website_button.click()
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.website_mode.isVisible())

        return tab

    def new_website_tab_with_files(self):
        tab = self.new_website_tab()

        # Add files
        for filename in self.tmpfiles:
            tab.website_mode.server_status.file_selection.file_list.add_file(filename)

        return tab

    def new_chat_tab(self):
        tab = self.gui.tabs.widget(0)
        self.verify_new_tab(tab)

        # Chat
        tab.chat_button.click()
        self.assertFalse(tab.new_tab.isVisible())
        self.assertTrue(tab.chat_mode.isVisible())

        return tab

    def close_all_tabs(self):
        for _ in range(self.gui.tabs.count()):
            tab = self.gui.tabs.widget(0)
            QtCore.QTimer.singleShot(200, tab.close_dialog.accept_button.click)
            self.gui.tabs.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).click()

    def gui_loaded(self):
        """Test that the GUI actually is shown"""
        self.assertTrue(self.gui.show)

    def window_title_seen(self):
        """Test that the window title is OnionShare"""
        self.assertEqual(self.gui.windowTitle(), "OnionShare")

    def server_status_bar_is_visible(self):
        """Test that the status bar is visible"""
        self.assertTrue(self.gui.status_bar.isVisible())

    def mode_settings_widget_is_visible(self, tab):
        """Test that the mode settings are visible"""
        self.assertTrue(tab.get_mode().mode_settings_widget.isVisible())

    def mode_settings_widget_is_hidden(self, tab):
        """Test that the mode settings are hidden when the server starts"""
        self.assertFalse(tab.get_mode().mode_settings_widget.isVisible())

    def click_toggle_history(self, tab):
        """Test that we can toggle Download or Upload history by clicking the toggle button"""
        currently_visible = tab.get_mode().history.isVisible()
        tab.get_mode().toggle_history.click()
        self.assertEqual(tab.get_mode().history.isVisible(), not currently_visible)

    def javascript_is_correct_mime_type(self, tab, file):
        """Test that the javascript file send.js is fetchable and that its MIME type is correct"""
        path = f"{tab.get_mode().web.static_url_path}/js/{file}"
        url = f"http://127.0.0.1:{tab.app.port}/{path}"
        r = requests.get(url)
        self.assertTrue(r.headers["Content-Type"].startswith("text/javascript;"))

    def history_indicator(self, tab, indicator_count="1"):
        """Test that we can make sure the history is toggled off, do an action, and the indicator works"""
        # Make sure history is toggled off
        if tab.get_mode().history.isVisible():
            tab.get_mode().toggle_history.click()
            self.assertFalse(tab.get_mode().history.isVisible())

        # Indicator should not be visible yet
        self.assertFalse(tab.get_mode().toggle_history.indicator_label.isVisible())

        if type(tab.get_mode()) == ReceiveMode:
            # Upload a file
            files = {"file[]": open(self.tmpfiles[0], "rb")}
            url = f"http://127.0.0.1:{tab.app.port}/upload"
            requests.post(url, files=files)
            QtTest.QTest.qWait(2000, self.gui.qtapp)

        if type(tab.get_mode()) == ShareMode:
            # Download files
            url = f"http://127.0.0.1:{tab.app.port}/download"
            requests.get(url)
            QtTest.QTest.qWait(2000, self.gui.qtapp)

        # Indicator should be visible, have a value of "1"
        self.assertTrue(tab.get_mode().toggle_history.indicator_label.isVisible())
        self.assertEqual(
            tab.get_mode().toggle_history.indicator_label.text(), indicator_count
        )

        # Toggle history back on, indicator should be hidden again
        tab.get_mode().toggle_history.click()
        self.assertFalse(tab.get_mode().toggle_history.indicator_label.isVisible())

    def history_is_not_visible(self, tab):
        """Test that the History section is not visible"""
        self.assertFalse(tab.get_mode().history.isVisible())

    def history_is_visible(self, tab):
        """Test that the History section is visible"""
        self.assertTrue(tab.get_mode().history.isVisible())

    def server_working_on_start_button_pressed(self, tab):
        """Test we can start the service"""
        # Should be in SERVER_WORKING state
        tab.get_mode().server_status.server_button.click()
        self.assertEqual(tab.get_mode().server_status.status, 1)

    def toggle_indicator_is_reset(self, tab):
        self.assertEqual(tab.get_mode().toggle_history.indicator_count, 0)
        self.assertFalse(tab.get_mode().toggle_history.indicator_label.isVisible())

    def server_status_indicator_says_starting(self, tab):
        """Test that the Server Status indicator shows we are Starting"""
        self.assertEqual(
            tab.get_mode().server_status_label.text(),
            strings._("gui_status_indicator_share_working"),
        )

    def server_status_indicator_says_scheduled(self, tab):
        """Test that the Server Status indicator shows we are Scheduled"""
        self.assertEqual(
            tab.get_mode().server_status_label.text(),
            strings._("gui_status_indicator_share_scheduled"),
        )

    def server_is_started(self, tab, startup_time=2000):
        """Test that the server has started"""
        QtTest.QTest.qWait(startup_time, self.gui.qtapp)
        # Should now be in SERVER_STARTED state
        self.assertEqual(tab.get_mode().server_status.status, 2)

    def web_server_is_running(self, tab):
        """Test that the web server has started"""
        try:
            requests.get(f"http://127.0.0.1:{tab.app.port}/")
            self.assertTrue(True)
        except requests.exceptions.ConnectionError:
            self.assertTrue(False)

    def add_button_visible(self, tab):
        """Test that the add button should be visible"""
        if platform.system() == "Darwin":
            self.assertTrue(
                tab.get_mode().server_status.file_selection.add_files_button.isVisible()
            )
            self.assertTrue(
                tab.get_mode().server_status.file_selection.add_folder_button.isVisible()
            )
        else:
            self.assertTrue(
                tab.get_mode().server_status.file_selection.add_button.isVisible()
            )

    def url_shown(self, tab):
        """Test that the URL is showing"""
        self.assertTrue(tab.get_mode().server_status.url.isVisible())

    def url_description_shown(self, tab):
        """Test that the URL label is showing"""
        self.assertTrue(tab.get_mode().server_status.url_description.isVisible())

    def url_instructions_shown(self, tab):
        """Test that the URL instructions for sharing are showing"""
        self.assertTrue(tab.get_mode().server_status.url_instructions.isVisible())

    def private_key_shown(self, tab):
        """Test that the Private Key is showing when not in public mode"""
        if not tab.settings.get("general", "public"):
            # Both the private key field and the toggle button should be seen
            self.assertTrue(tab.get_mode().server_status.private_key.isVisible())
            self.assertTrue(
                tab.get_mode().server_status.client_auth_toggle_button.isVisible()
            )
            self.assertEqual(
                tab.get_mode().server_status.client_auth_toggle_button.text(),
                strings._("gui_reveal"),
            )

            # Test that the key is masked unless Reveal is clicked
            self.assertEqual(
                tab.get_mode().server_status.private_key.text(),
                "*" * len(tab.app.auth_string),
            )

            # Click reveal
            tab.get_mode().server_status.client_auth_toggle_button.click()

            # The real private key should be revealed
            self.assertEqual(
                tab.get_mode().server_status.private_key.text(), tab.app.auth_string
            )
            self.assertEqual(
                tab.get_mode().server_status.client_auth_toggle_button.text(),
                strings._("gui_hide"),
            )

            # Click hide, key should be masked again
            tab.get_mode().server_status.client_auth_toggle_button.click()
            self.assertEqual(
                tab.get_mode().server_status.private_key.text(),
                "*" * len(tab.app.auth_string),
            )
            self.assertEqual(
                tab.get_mode().server_status.client_auth_toggle_button.text(),
                strings._("gui_reveal"),
            )
        else:
            self.assertFalse(tab.get_mode().server_status.private_key.isVisible())

    def client_auth_instructions_shown(self, tab):
        """
        Test that the Private Key instructions for sharing
        are showing when not in public mode
        """
        if not tab.settings.get("general", "public"):
            self.assertTrue(
                tab.get_mode().server_status.client_auth_instructions.isVisible()
            )
        else:
            self.assertFalse(
                tab.get_mode().server_status.client_auth_instructions.isVisible()
            )

    def have_copy_url_button(self, tab):
        """Test that the Copy URL button is shown and that the clipboard is correct"""
        self.assertTrue(tab.get_mode().server_status.copy_url_button.isVisible())

        tab.get_mode().server_status.copy_url_button.click()
        clipboard = tab.common.gui.qtapp.clipboard()
        self.assertEqual(clipboard.text(), f"http://127.0.0.1:{tab.app.port}")

    def have_show_url_qr_code_button(self, tab):
        """Test that the Show QR Code URL button is shown and that it loads a QR Code Dialog"""
        self.assertTrue(
            tab.get_mode().server_status.show_url_qr_code_button.isVisible()
        )

        def accept_dialog():
            window = tab.common.gui.qtapp.activeWindow()
            if window:
                window.close()

        QtCore.QTimer.singleShot(500, accept_dialog)
        tab.get_mode().server_status.show_url_qr_code_button.click()

    def have_show_client_auth_qr_code_button(self, tab):
        """
        Test that the Show QR Code Client Auth button is shown when
        not in public mode and that it loads a QR Code Dialog.
        """
        if not tab.settings.get("general", "public"):
            self.assertTrue(
                tab.get_mode().server_status.show_client_auth_qr_code_button.isVisible()
            )

            def accept_dialog():
                window = tab.common.gui.qtapp.activeWindow()
                if window:
                    window.close()

            QtCore.QTimer.singleShot(500, accept_dialog)
            tab.get_mode().server_status.show_client_auth_qr_code_button.click()
        else:
            self.assertFalse(
                tab.get_mode().server_status.show_client_auth_qr_code_button.isVisible()
            )

    def server_status_indicator_says_started(self, tab):
        """Test that the Server Status indicator shows we are started"""
        if type(tab.get_mode()) == ReceiveMode:
            self.assertEqual(
                tab.get_mode().server_status_label.text(),
                strings._("gui_status_indicator_receive_started"),
            )
        if type(tab.get_mode()) == ShareMode:
            self.assertEqual(
                tab.get_mode().server_status_label.text(),
                strings._("gui_status_indicator_share_started"),
            )

    def web_page(self, tab, string):
        """Test that the web page contains a string"""

        url = f"http://127.0.0.1:{tab.app.port}/"
        r = requests.get(url)
        self.assertTrue(string in r.text)

    def history_widgets_present(self, tab):
        """Test that the relevant widgets are present in the history view after activity has taken place"""
        self.assertFalse(tab.get_mode().history.empty.isVisible())
        self.assertTrue(tab.get_mode().history.not_empty.isVisible())

    def counter_incremented(self, tab, count):
        """Test that the counter has incremented"""
        self.assertEqual(tab.get_mode().history.completed_count, count)

    def server_is_stopped(self, tab):
        """Test that the server stops when we click Stop"""
        if (
            type(tab.get_mode()) == ReceiveMode
            or (
                type(tab.get_mode()) == ShareMode
                and not tab.settings.get("share", "autostop_sharing")
            )
            or (type(tab.get_mode()) == WebsiteMode)
            or (type(tab.get_mode()) == ChatMode)
        ):
            tab.get_mode().server_status.server_button.click()
        self.assertEqual(tab.get_mode().server_status.status, 0)
        self.assertFalse(
            tab.get_mode().server_status.show_url_qr_code_button.isVisible()
        )
        self.assertFalse(tab.get_mode().server_status.copy_url_button.isVisible())
        self.assertFalse(tab.get_mode().server_status.url.isVisible())
        self.assertFalse(tab.get_mode().server_status.url_description.isVisible())
        self.assertFalse(tab.get_mode().server_status.url_instructions.isVisible())
        self.assertFalse(tab.get_mode().server_status.private_key.isVisible())
        self.assertFalse(
            tab.get_mode().server_status.client_auth_instructions.isVisible()
        )
        self.assertFalse(
            tab.get_mode().server_status.copy_client_auth_button.isVisible()
        )

    def web_server_is_stopped(self, tab):
        """Test that the web server also stopped"""
        QtTest.QTest.qWait(800, self.gui.qtapp)

        try:
            requests.get(f"http://127.0.0.1:{tab.app.port}/")
            self.assertTrue(False)
        except requests.exceptions.ConnectionError:
            self.assertTrue(True)

    def server_status_indicator_says_closed(self, tab):
        """Test that the Server Status indicator shows we closed"""
        if type(tab.get_mode()) == ReceiveMode:
            self.assertEqual(
                tab.get_mode().server_status_label.text(),
                strings._("gui_status_indicator_receive_stopped"),
            )
        if type(tab.get_mode()) == ShareMode:
            if not tab.settings.get("share", "autostop_sharing"):
                self.assertEqual(
                    tab.get_mode().server_status_label.text(),
                    strings._("gui_status_indicator_share_stopped"),
                )
            else:
                self.assertEqual(
                    tab.get_mode().server_status_label.text(),
                    strings._("closing_automatically"),
                )

    def clear_all_history_items(self, tab, count):
        if count == 0:
            tab.get_mode().history.clear_button.click()
        self.assertEqual(len(tab.get_mode().history.item_list.items.keys()), count)

    def file_selection_widget_has_files(self, tab, num=3):
        """Test that the number of items in the list is as expected"""
        self.assertEqual(
            tab.get_mode().server_status.file_selection.get_num_files(), num
        )

    def add_remove_buttons_hidden(self, tab):
        """Test that the add and remove buttons are hidden when the server starts"""
        if platform.system() == "Darwin":
            self.assertFalse(
                tab.get_mode().server_status.file_selection.add_files_button.isVisible()
            )
            self.assertFalse(
                tab.get_mode().server_status.file_selection.add_folder_button.isVisible()
            )
        else:
            self.assertFalse(
                tab.get_mode().server_status.file_selection.add_button.isVisible()
            )
        self.assertFalse(
            tab.get_mode().server_status.file_selection.remove_button.isVisible()
        )

    # Auto-stop timer tests
    def set_timeout(self, tab, timeout):
        """Test that the timeout can be set"""
        timer = QtCore.QDateTime.currentDateTime().addSecs(timeout)
        tab.get_mode().mode_settings_widget.autostop_timer_widget.setDateTime(timer)
        self.assertTrue(
            tab.get_mode().mode_settings_widget.autostop_timer_widget.dateTime(), timer
        )

    def autostop_timer_widget_hidden(self, tab):
        """Test that the auto-stop timer widget is hidden when share has started"""
        self.assertFalse(
            tab.get_mode().mode_settings_widget.autostop_timer_widget.isVisible()
        )

    def server_timed_out(self, tab, wait):
        """Test that the server has timed out after the timer ran out"""
        QtTest.QTest.qWait(wait, self.gui.qtapp)
        # We should have timed out now
        self.assertEqual(tab.get_mode().server_status.status, 0)

    def clientauth_is_visible(self, tab):
        """Test that the ClientAuth button is visible and that the clipboard contains its contents"""
        self.assertTrue(
            tab.get_mode().server_status.copy_client_auth_button.isVisible()
        )
        tab.get_mode().server_status.copy_client_auth_button.click()
        clipboard = tab.common.gui.qtapp.clipboard()
        self.assertEqual(
            clipboard.text(), "E2GOT5LTUTP3OAMRCRXO4GSH6VKJEUOXZQUC336SRKAHTTT5OVSA"
        )

    def clientauth_is_not_visible(self, tab):
        """Test that the ClientAuth button is not visible"""
        self.assertFalse(
            tab.get_mode().server_status.copy_client_auth_button.isVisible()
        )

    def hit_405(self, url, expected_resp, data={}, methods=[]):
        """Test various HTTP methods and the response"""
        for method in methods:
            if method == "put":
                r = requests.put(url, data=data)
            if method == "post":
                r = requests.post(url, data=data)
            if method == "delete":
                r = requests.delete(url)
            if method == "options":
                r = requests.options(url)
            self.assertTrue(expected_resp in r.text)
            self.assertFalse("Werkzeug" in r.headers)

    # Grouped tests follow from here

    def run_all_common_setup_tests(self):
        self.gui_loaded()
        self.window_title_seen()
        self.server_status_bar_is_visible()
