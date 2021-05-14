import requests

from PySide2 import QtTest

from .gui_base_test import GuiBaseTest


class TestChat(GuiBaseTest):
    # Shared test methods

    def view_chat(self, tab):
        """Test that we can view the chat room"""
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
        self.assertTrue("Chat <b>requires JavaScript</b>" in r.text)

        cookies_dict = requests.utils.dict_from_cookiejar(r.cookies)
        self.assertTrue("session" in cookies_dict.keys())

    def change_username(self, tab):
        """Test that we can change our username"""
        url = f"http://127.0.0.1:{tab.app.port}/update-session-username"
        data = {"username":"oniontest"}
        if tab.settings.get("general", "public"):
            r = requests.post(url, json=data)
        else:
            r = requests.post(
                url,
                json=data,
                auth=requests.auth.HTTPBasicAuth(
                    "onionshare", tab.get_mode().server_status.web.password
                ),
            )

        QtTest.QTest.qWait(500, self.gui.qtapp)
        jsonResponse = r.json()
        self.assertTrue(jsonResponse["success"])
        self.assertEqual(jsonResponse["username"], "oniontest")

    def change_username_too_long(self, tab):
        """Test that we can't set our username to something 128 chars or longer"""
        url = f"http://127.0.0.1:{tab.app.port}/update-session-username"
        bad_username = "sduBB9yEMkyQpwkMM4A9nUbQwNUbPU2PQuJYN26zCQ4inELpB76J5i5oRUnD3ESVaE9NNE8puAtBj2DiqDaZdVqhV8MonyxSSGHRv87YgM5dzwBYPBxttoQSKZAUkFjo"
        data = {"username":bad_username}
        if tab.settings.get("general", "public"):
            r = requests.post(url, json=data)
        else:
            r = requests.post(
                url,
                json=data,
                auth=requests.auth.HTTPBasicAuth(
                    "onionshare", tab.get_mode().server_status.web.password
                ),
            )

        QtTest.QTest.qWait(500, self.gui.qtapp)
        jsonResponse = r.json()
        self.assertFalse(jsonResponse["success"])
        self.assertNotEqual(jsonResponse["username"], bad_username)

    def run_all_chat_mode_tests(self, tab):
        """Tests in chat mode after starting a chat"""
        self.server_working_on_start_button_pressed(tab)
        self.server_status_indicator_says_starting(tab)
        self.server_is_started(tab, startup_time=500)
        self.web_server_is_running(tab)
        self.have_a_password(tab)
        self.url_description_shown(tab)
        self.have_copy_url_button(tab)
        self.have_show_qr_code_button(tab)
        self.server_status_indicator_says_started(tab)
        self.view_chat(tab)
        self.change_username(tab)
        self.change_username_too_long(tab)
        self.server_is_stopped(tab)
        self.web_server_is_stopped(tab)
        self.server_status_indicator_says_closed(tab)

    # Tests

    def test_chat(self):
        """
        Test chat mode
        """
        tab = self.new_chat_tab()
        self.run_all_chat_mode_tests(tab)
        self.close_all_tabs()
