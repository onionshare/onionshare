import requests
import zipfile
from PyQt5 import QtTest
from .TorGuiBaseTest import TorGuiBaseTest
from .GuiShareTest import GuiShareTest

class TorGuiShareTest(TorGuiBaseTest, GuiShareTest):
    def download_share(self, public_mode):
        '''Test downloading a share'''
        # Set up connecting to the onion
        (socks_address, socks_port) = self.gui.app.onion.get_tor_socks_port()
        session = requests.session()
        session.proxies = {}
        session.proxies['http'] = 'socks5h://{}:{}'.format(socks_address, socks_port)

        # Download files
        if public_mode:
            path = "http://{}/download".format(self.gui.app.onion_host)
        else:
            path = "http://{}/{}/download".format(self.gui.app.onion_host, self.gui.share_mode.web.slug)
        response = session.get(path, stream=True)
        QtTest.QTest.qWait(4000)

        if response.status_code == 200:
            with open('/tmp/download.zip', 'wb') as file_to_write:
                for chunk in response.iter_content(chunk_size=128):
                    file_to_write.write(chunk)
                file_to_write.close()
            zip = zipfile.ZipFile('/tmp/download.zip')
        QtTest.QTest.qWait(4000)
        self.assertEqual('onionshare', zip.read('test.txt').decode('utf-8'))


    # Persistence tests
    def have_same_onion(self, onion):
        '''Test that we have the same onion'''
        self.assertEqual(self.gui.app.onion_host, onion)

    # legacy v2 onion test
    def have_v2_onion(self):
        '''Test that the onion is a v2 style onion'''
        self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')
        self.assertEqual(len(self.gui.app.onion_host), 22)

    # 'Grouped' tests follow from here

    def run_all_share_mode_started_tests(self, public_mode):
        '''Tests in share mode after starting a share'''
        self.server_working_on_start_button_pressed(self.gui.share_mode)
        self.server_status_indicator_says_starting(self.gui.share_mode)
        self.add_delete_buttons_hidden()
        self.settings_button_is_hidden()
        self.server_is_started(self.gui.share_mode, startup_time=45000)
        self.web_server_is_running()
        self.have_an_onion_service()
        self.have_a_slug(self.gui.share_mode, public_mode)
        self.url_description_shown(self.gui.share_mode)
        self.have_copy_url_button(self.gui.share_mode, public_mode)
        self.server_status_indicator_says_started(self.gui.share_mode)


    def run_all_share_mode_download_tests(self, public_mode, stay_open):
        """Tests in share mode after downloading a share"""
        self.web_page(self.gui.share_mode, 'Total size', public_mode)
        self.download_share(public_mode)
        self.history_widgets_present(self.gui.share_mode)
        self.server_is_stopped(self.gui.share_mode, stay_open)
        self.web_server_is_stopped()
        self.server_status_indicator_says_closed(self.gui.share_mode, stay_open)
        self.add_button_visible()
        self.server_working_on_start_button_pressed(self.gui.share_mode)
        self.server_is_started(self.gui.share_mode, startup_time=45000)
        self.history_indicator(self.gui.share_mode, public_mode)


    def run_all_share_mode_persistent_tests(self, public_mode, stay_open):
        """Same as end-to-end share tests but also test the slug is the same on multiple shared"""
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(public_mode)
        slug = self.gui.share_mode.server_status.web.slug
        onion = self.gui.app.onion_host
        self.run_all_share_mode_download_tests(public_mode, stay_open)
        self.have_same_onion(onion)
        self.have_same_slug(slug)

    
    def run_all_share_mode_timer_tests(self, public_mode):
        """Auto-stop timer tests in share mode"""
        self.run_all_share_mode_setup_tests()
        self.set_timeout(self.gui.share_mode, 120)
        self.run_all_share_mode_started_tests(public_mode)
        self.autostop_timer_widget_hidden(self.gui.share_mode)
        self.server_timed_out(self.gui.share_mode, 125000)
        self.web_server_is_stopped()

