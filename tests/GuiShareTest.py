import socks
import zipfile
from PyQt5 import QtCore, QtTest
from .GuiBaseTest import GuiBaseTest

class GuiShareTest(GuiBaseTest):
    # Auto-stop timer tests
    
    def set_timeout(self, mode, timeout):
        '''Test that the timeout can be set'''
        timer = QtCore.QDateTime.currentDateTime().addSecs(timeout)
        mode.server_status.shutdown_timeout.setDateTime(timer)
        self.assertTrue(mode.server_status.shutdown_timeout.dateTime(), timer)

    
    def timeout_widget_hidden(self, mode):
        '''Test that the timeout widget is hidden when share has started'''
        self.assertFalse(mode.server_status.shutdown_timeout_container.isVisible())

    
    def server_timed_out(self, mode, wait):
        '''Test that the server has timed out after the timer ran out'''
        QtTest.QTest.qWait(wait)
        # We should have timed out now
        self.assertEqual(mode.server_status.status, 0)

    # Persistence tests
    def have_same_slug(self, slug):
        '''Test that we have the same slug'''
        self.assertEqual(self.gui.share_mode.server_status.web.slug, slug)

    # Share-specific tests
    
    def file_selection_widget_has_a_file(self):
        '''Test that the number of files in the list is 1'''
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), 1)

    
    def deleting_only_file_hides_delete_button(self):
        '''Test that clicking on the file item shows the delete button. Test that deleting the only item in the list hides the delete button'''
        rect = self.gui.share_mode.server_status.file_selection.file_list.visualItemRect(self.gui.share_mode.server_status.file_selection.file_list.item(0))
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.viewport(), QtCore.Qt.LeftButton, pos=rect.center())
        # Delete button should be visible
        self.assertTrue(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())
        # Click delete, and since there's no more files, the delete button should be hidden
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.delete_button, QtCore.Qt.LeftButton)
        self.assertFalse(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())

    
    def add_a_file_and_delete_using_its_delete_widget(self):
        '''Test that we can also delete a file by clicking on its [X] widget'''
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/etc/hosts')
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.item(0).item_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), 0)

    
    def file_selection_widget_readd_files(self):
        '''Re-add some files to the list so we can share'''
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/etc/hosts')
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/tmp/test.txt')
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), 2)

    
    def add_delete_buttons_hidden(self):
        '''Test that the add and delete buttons are hidden when the server starts'''
        self.assertFalse(self.gui.share_mode.server_status.file_selection.add_button.isVisible())
        self.assertFalse(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())

    
    def download_share(self, public_mode):
        '''Test that we can download the share'''
        s = socks.socksocket()
        s.settimeout(60)
        s.connect(('127.0.0.1', self.gui.app.port))

        if public_mode:
            path = '/download'
        else:
            path = '{}/download'.format(self.gui.share_mode.web.slug)

        http_request = 'GET {} HTTP/1.0\r\n'.format(path)
        http_request += 'Host: 127.0.0.1\r\n'
        http_request += '\r\n'
        s.sendall(http_request.encode('utf-8'))

        with open('/tmp/download.zip', 'wb') as file_to_write:
            while True:
               data = s.recv(1024)
               if not data:
                   break
               file_to_write.write(data)
            file_to_write.close()

        zip = zipfile.ZipFile('/tmp/download.zip')
        QtTest.QTest.qWait(2000)
        self.assertEqual('onionshare', zip.read('test.txt').decode('utf-8'))

    
    def add_button_visible(self):
        '''Test that the add button should be visible'''
        self.assertTrue(self.gui.share_mode.server_status.file_selection.add_button.isVisible())


    def run_all_share_mode_setup_tests(self):
        """Tests in share mode prior to starting a share"""
        self.click_mode(self.gui.share_mode)
        self.file_selection_widget_has_a_file()
        self.history_is_not_visible(self.gui.share_mode)
        self.click_toggle_history(self.gui.share_mode)
        self.history_is_visible(self.gui.share_mode)
        self.deleting_only_file_hides_delete_button()
        self.add_a_file_and_delete_using_its_delete_widget()
        self.file_selection_widget_readd_files()

    
    def run_all_share_mode_started_tests(self, public_mode):
        """Tests in share mode after starting a share"""
        self.server_working_on_start_button_pressed(self.gui.share_mode)
        self.server_status_indicator_says_starting(self.gui.share_mode)
        self.add_delete_buttons_hidden()
        self.settings_button_is_hidden()
        self.a_server_is_started(self.gui.share_mode)
        self.a_web_server_is_running()
        self.have_a_slug(self.gui.share_mode, public_mode)
        self.url_description_shown(self.gui.share_mode)
        self.have_copy_url_button(self.gui.share_mode)
        self.server_status_indicator_says_started(self.gui.share_mode)

    
    def run_all_share_mode_download_tests(self, public_mode, stay_open):
        """Tests in share mode after downloading a share"""
        self.web_page(self.gui.share_mode, 'Total size', public_mode)
        self.download_share(public_mode)
        self.history_widgets_present(self.gui.share_mode)
        self.server_is_stopped(self.gui.share_mode, stay_open)
        self.web_service_is_stopped()
        self.server_status_indicator_says_closed(self.gui.share_mode, stay_open)
        self.add_button_visible()
        self.server_working_on_start_button_pressed(self.gui.share_mode)
        self.a_server_is_started(self.gui.share_mode)
        self.history_indicator(self.gui.share_mode, public_mode)

    
    def run_all_share_mode_tests(self, public_mode, stay_open):
        """End-to-end share tests"""
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(public_mode)
        self.run_all_share_mode_download_tests(public_mode, stay_open)


    def run_all_share_mode_persistent_tests(self, public_mode, stay_open):
        """Same as end-to-end share tests but also test the slug is the same on multiple shared"""
        self.run_all_share_mode_setup_tests()
        self.run_all_share_mode_started_tests(public_mode)
        slug = self.gui.share_mode.server_status.web.slug
        self.run_all_share_mode_download_tests(public_mode, stay_open)
        self.have_same_slug(slug)


    def run_all_share_mode_timer_tests(self, public_mode):
        """Auto-stop timer tests in share mode"""
        self.run_all_share_mode_setup_tests()
        self.set_timeout(self.gui.share_mode, 5)
        self.run_all_share_mode_started_tests(public_mode)
        self.timeout_widget_hidden(self.gui.share_mode)
        self.server_timed_out(self.gui.share_mode, 10000)
        self.web_service_is_stopped()

