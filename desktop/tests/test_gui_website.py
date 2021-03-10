import requests

from PySide2 import QtTest

from .gui_base_test import GuiBaseTest


class TestWebsite(GuiBaseTest):
    # Shared test methods

    def view_website(self, tab):
        """Test that we can download the share"""
        url = f"http://127.0.0.1:{tab.app.port}/"
        if tab.settings.get("general", "public"):
            r = requests.get(url)
        else:
            r = requests.get(
                url,
                auth=requests.auth.HTTPBasicAuth(
                    "onionshare", tab.get_mode().server_status.web.password
                ),
            )

        QtTest.QTest.qWait(500, self.gui.qtapp)
        self.assertTrue("This is a test website hosted by OnionShare" in r.text)

    def check_csp_header(self, tab):
        """Test that the CSP header is present when enabled or vice versa"""
        url = f"http://127.0.0.1:{tab.app.port}/"
        if tab.settings.get("general", "public"):
            r = requests.get(url)
        else:
            r = requests.get(
                url,
                auth=requests.auth.HTTPBasicAuth(
                    "onionshare", tab.get_mode().server_status.web.password
                ),
            )

        QtTest.QTest.qWait(500, self.gui.qtapp)
        if tab.settings.get("website", "disable_csp"):
            self.assertFalse("Content-Security-Policy" in r.headers)
        else:
            self.assertTrue("Content-Security-Policy" in r.headers)

    def run_all_website_mode_setup_tests(self, tab):
        """Tests in website mode prior to starting a share"""
        tab.get_mode().server_status.file_selection.file_list.add_file(
            self.tmpfile_index_html
        )
        for filename in self.tmpfiles:
            tab.get_mode().server_status.file_selection.file_list.add_file(filename)

        self.file_selection_widget_has_files(tab, 11)
        self.history_is_not_visible(tab)
        self.click_toggle_history(tab)
        self.history_is_visible(tab)

    def run_all_website_mode_started_tests(self, tab, startup_time=500):
        """Tests in website mode after starting a share"""
        self.server_working_on_start_button_pressed(tab)
        self.server_status_indicator_says_starting(tab)
        self.add_remove_buttons_hidden(tab)
        self.server_is_started(tab, startup_time)
        self.web_server_is_running(tab)
        self.have_a_password(tab)
        self.url_description_shown(tab)
        self.have_copy_url_button(tab)
        self.have_show_qr_code_button(tab)
        self.server_status_indicator_says_started(tab)

    def run_all_website_mode_download_tests(self, tab):
        """Tests in website mode after viewing the site"""
        self.run_all_website_mode_setup_tests(tab)
        self.run_all_website_mode_started_tests(tab, startup_time=500)
        self.view_website(tab)
        self.check_csp_header(tab)
        self.history_widgets_present(tab)
        self.server_is_stopped(tab)
        self.web_server_is_stopped(tab)
        self.server_status_indicator_says_closed(tab)
        self.add_button_visible(tab)

    # Tests

    def test_website(self):
        """
        Test website mode
        """
        tab = self.new_website_tab()
        self.run_all_website_mode_download_tests(tab)
        self.close_all_tabs()

    def test_csp_enabled(self):
        """
        Test disabling CSP
        """
        tab = self.new_website_tab()
        tab.get_mode().disable_csp_checkbox.click()
        self.run_all_website_mode_download_tests(tab)
        self.close_all_tabs()
