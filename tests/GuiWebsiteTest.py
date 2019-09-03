import json
import os
import requests
import socks
import zipfile
import tempfile
from PyQt5 import QtCore, QtTest
from onionshare import strings
from onionshare.common import Common
from onionshare.settings import Settings
from onionshare.onion import Onion
from onionshare.web import Web
from onionshare_gui import Application, OnionShare, OnionShareGui
from .GuiShareTest import GuiShareTest

class GuiWebsiteTest(GuiShareTest):
    @staticmethod
    def set_up(test_settings):
        '''Create GUI with given settings'''
        # Create our test file
        testfile = open('/tmp/index.html', 'w')
        testfile.write('<html><blink>This is a test website hosted by OnionShare</blink></html>')
        testfile.close()

        common = Common()
        common.settings = Settings(common)
        common.define_css()
        strings.load_strings(common)

        # Get all of the settings in test_settings
        test_settings['data_dir'] = '/tmp/OnionShare'
        for key, val in common.settings.default_settings.items():
            if key not in test_settings:
                test_settings[key] = val

        # Start the Onion
        testonion = Onion(common)
        global qtapp
        qtapp = Application(common)
        app = OnionShare(common, testonion, True, 0)

        web = Web(common, False, True)
        open('/tmp/settings.json', 'w').write(json.dumps(test_settings))

        gui = OnionShareGui(common, testonion, qtapp, app, ['/tmp/index.html'], '/tmp/settings.json', True)
        return gui

    @staticmethod
    def tear_down():
        '''Clean up after tests'''
        try:
            os.remove('/tmp/index.html')
            os.remove('/tmp/settings.json')
        except:
            pass


    def view_website(self, public_mode):
        '''Test that we can download the share'''
        url = "http://127.0.0.1:{}/".format(self.gui.app.port)
        if public_mode:
            r = requests.get(url)
        else:
            r = requests.get(url, auth=requests.auth.HTTPBasicAuth('onionshare', self.gui.website_mode.server_status.web.password))

        QtTest.QTest.qWait(2000)
        self.assertTrue('<blink>This is a test website hosted by OnionShare</blink>' in r.text)

    def run_all_website_mode_setup_tests(self):
        """Tests in website mode prior to starting a share"""
        self.click_mode(self.gui.website_mode)
        self.file_selection_widget_has_files(1)
        self.history_is_not_visible(self.gui.website_mode)
        self.click_toggle_history(self.gui.website_mode)
        self.history_is_visible(self.gui.website_mode)

    def run_all_website_mode_started_tests(self, public_mode, startup_time=2000):
        """Tests in website mode after starting a share"""
        self.server_working_on_start_button_pressed(self.gui.website_mode)
        self.server_status_indicator_says_starting(self.gui.website_mode)
        self.add_delete_buttons_hidden()
        self.settings_button_is_hidden()
        self.server_is_started(self.gui.website_mode, startup_time)
        self.web_server_is_running()
        self.have_a_password(self.gui.website_mode, public_mode)
        self.url_description_shown(self.gui.website_mode)
        self.have_copy_url_button(self.gui.website_mode, public_mode)
        self.server_status_indicator_says_started(self.gui.website_mode)


    def run_all_website_mode_download_tests(self, public_mode, stay_open):
        """Tests in website mode after viewing the site"""
        self.run_all_website_mode_setup_tests()
        self.run_all_website_mode_started_tests(public_mode, startup_time=2000)
        self.view_website(public_mode)
        self.history_widgets_present(self.gui.website_mode)

