import requests

from PySide2 import QtTest

from .gui_base_test import GuiBaseTest


class TestChat(GuiBaseTest):
    # Shared test methods

    def view_chat(self, tab):
        """Test that we can view the chat room"""
        url = f"http://127.0.0.1:{tab.app.port}/"
        r = requests.get(url)

        QtTest.QTest.qWait(500, self.gui.qtapp)
        self.assertTrue("Chat <b>requires JavaScript</b>" in r.text)

        cookies_dict = requests.utils.dict_from_cookiejar(r.cookies)
        self.assertTrue("session" in cookies_dict.keys())

    def change_username(self, tab):
        """Test that we can change our username"""
        url = f"http://127.0.0.1:{tab.app.port}/update-session-username"
        data = {"username": "oniontest"}
        r = requests.post(url, json=data)

        QtTest.QTest.qWait(500, self.gui.qtapp)
        jsonResponse = r.json()
        self.assertTrue(jsonResponse["success"])
        self.assertEqual(jsonResponse["username"], "oniontest")

    def run_all_chat_mode_started_tests(self, tab):
        """Tests in chat mode after starting a chat"""
        self.server_working_on_start_button_pressed(tab)
        self.server_status_indicator_says_starting(tab)
        self.server_is_started(tab, startup_time=500)
        self.web_server_is_running(tab)
        self.url_description_shown(tab)
        self.url_instructions_shown(tab)
        self.url_shown(tab)
        self.have_copy_url_button(tab)
        self.have_show_url_qr_code_button(tab)
        self.private_key_shown(tab)
        self.client_auth_instructions_shown(tab)
        self.have_show_client_auth_qr_code_button(tab)
        self.server_status_indicator_says_started(tab)

    def run_all_chat_mode_stopping_tests(self, tab):
        """Tests stopping a chat"""
        self.server_is_stopped(tab)
        self.web_server_is_stopped(tab)
        self.server_status_indicator_says_closed(tab)

    # Tests

    def test_chat(self):
        """
        Test chat mode
        """
        tab = self.new_chat_tab()
        self.run_all_chat_mode_started_tests(tab)
        self.view_chat(tab)
        self.javascript_is_correct_mime_type(tab, "chat.js")
        self.change_username(tab)
        self.run_all_chat_mode_stopping_tests(tab)
        self.close_all_tabs()

    def test_405_page_returned_for_invalid_methods(self):
        """
        Our custom 405 page should return for invalid methods
        """
        tab = self.new_chat_tab()

        tab.get_mode().mode_settings_widget.public_checkbox.click()

        self.run_all_chat_mode_started_tests(tab)
        url = f"http://127.0.0.1:{tab.app.port}/"
        self.hit_405(
            url,
            expected_resp="OnionShare: 405 Method Not Allowed",
            data={"foo": "bar"},
            methods=["put", "post", "delete", "options"],
        )
        self.run_all_chat_mode_stopping_tests(tab)
        self.close_all_tabs()
