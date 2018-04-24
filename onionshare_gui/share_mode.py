# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from .mode import Mode

class ShareMode(QtWidgets.QWidget):
    """
    Parts of the main window UI for sharing files.
    """
    def __init__(self, common):
        super(ShareMode, self).__init__()
        self.common = common

        # File selection
        self.file_selection = FileSelection(self.common)
        if filenames:
            for filename in filenames:
                self.file_selection.file_list.add_file(filename)

        # Server status
        self.server_status = ServerStatus(self.common, self.qtapp, self.app, self.web, self.file_selection)
        self.server_status.server_started.connect(self.file_selection.server_started)
        self.server_status.server_started.connect(self.start_server)
        self.server_status.server_started.connect(self.update_server_status_indicator)
        self.server_status.server_stopped.connect(self.file_selection.server_stopped)
        self.server_status.server_stopped.connect(self.stop_server)
        self.server_status.server_stopped.connect(self.update_server_status_indicator)
        self.server_status.server_stopped.connect(self.update_primary_action)
        self.server_status.server_canceled.connect(self.cancel_server)
        self.server_status.server_canceled.connect(self.file_selection.server_stopped)
        self.server_status.server_canceled.connect(self.update_primary_action)
        self.start_server_finished.connect(self.clear_message)
        self.start_server_finished.connect(self.server_status.start_server_finished)
        self.start_server_finished.connect(self.update_server_status_indicator)
        self.stop_server_finished.connect(self.server_status.stop_server_finished)
        self.stop_server_finished.connect(self.update_server_status_indicator)
        self.file_selection.file_list.files_updated.connect(self.server_status.update)
        self.file_selection.file_list.files_updated.connect(self.update_primary_action)
        self.server_status.url_copied.connect(self.copy_url)
        self.server_status.hidservauth_copied.connect(self.copy_hidservauth)
        self.starting_server_step2.connect(self.start_server_step2)
        self.starting_server_step3.connect(self.start_server_step3)
        self.starting_server_error.connect(self.start_server_error)
        self.server_status.button_clicked.connect(self.clear_message)

        # Filesize warning
        self.filesize_warning = QtWidgets.QLabel()
        self.filesize_warning.setWordWrap(True)
        self.filesize_warning.setStyleSheet('padding: 10px 0; font-weight: bold; color: #333333;')
        self.filesize_warning.hide()

        # Downloads
        self.downloads = Downloads(self.common)
        self.new_download = False
        self.downloads_in_progress = 0
        self.downloads_completed = 0

        # Info label along top of screen
        self.info_layout = QtWidgets.QHBoxLayout()
        self.info_label = QtWidgets.QLabel()
        self.info_label.setStyleSheet('QLabel { font-size: 12px; color: #666666; }')

        self.info_show_downloads = QtWidgets.QToolButton()
        self.info_show_downloads.setIcon(QtGui.QIcon(self.common.get_resource_path('images/download_window_gray.png')))
        self.info_show_downloads.setCheckable(True)
        self.info_show_downloads.toggled.connect(self.downloads_toggled)
        self.info_show_downloads.setToolTip(strings._('gui_downloads_window_tooltip', True))

        self.info_in_progress_downloads_count = QtWidgets.QLabel()
        self.info_in_progress_downloads_count.setStyleSheet('QLabel { font-size: 12px; color: #666666; }')

        self.info_completed_downloads_count = QtWidgets.QLabel()
        self.info_completed_downloads_count.setStyleSheet('QLabel { font-size: 12px; color: #666666; }')

        self.update_downloads_completed(self.downloads_in_progress)
        self.update_downloads_in_progress(self.downloads_in_progress)

        self.info_layout.addWidget(self.info_label)
        self.info_layout.addStretch()
        self.info_layout.addWidget(self.info_in_progress_downloads_count)
        self.info_layout.addWidget(self.info_completed_downloads_count)
        self.info_layout.addWidget(self.info_show_downloads)

        self.info_widget = QtWidgets.QWidget()
        self.info_widget.setLayout(self.info_layout)
        self.info_widget.hide()

        # Server status indicator on the status bar
        self.server_status_image_stopped = QtGui.QImage(self.common.get_resource_path('images/server_stopped.png'))
        self.server_status_image_working = QtGui.QImage(self.common.get_resource_path('images/server_working.png'))
        self.server_status_image_started = QtGui.QImage(self.common.get_resource_path('images/server_started.png'))
        self.server_status_image_label = QtWidgets.QLabel()
        self.server_status_image_label.setFixedWidth(20)
        self.server_status_label = QtWidgets.QLabel()
        self.server_status_label.setStyleSheet('QLabel { font-style: italic; color: #666666; }')
        server_status_indicator_layout = QtWidgets.QHBoxLayout()
        server_status_indicator_layout.addWidget(self.server_status_image_label)
        server_status_indicator_layout.addWidget(self.server_status_label)
        self.server_status_indicator = QtWidgets.QWidget()
        self.server_status_indicator.setLayout(server_status_indicator_layout)
        self.update_server_status_indicator()

        # Primary action layout
        primary_action_layout = QtWidgets.QVBoxLayout()
        primary_action_layout.addWidget(self.server_status)
        primary_action_layout.addWidget(self.filesize_warning)
        self.primary_action = QtWidgets.QWidget()
        self.primary_action.setLayout(primary_action_layout)
        self.primary_action.hide()
        self.update_primary_action()

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.info_widget)
        layout.addLayout(self.file_selection)
        layout.addWidget(self.primary_action)
        self.setLayout(layout)

        # Always start with focus on file selection
        self.file_selection.setFocus()

    def update_primary_action(self):
        # Show or hide primary action layout
        file_count = self.file_selection.file_list.count()
        if file_count > 0:
            self.primary_action.show()
            self.info_widget.show()

            # Update the file count in the info label
            total_size_bytes = 0
            for index in range(self.file_selection.file_list.count()):
                item = self.file_selection.file_list.item(index)
                total_size_bytes += item.size_bytes
            total_size_readable = self.common.human_readable_filesize(total_size_bytes)

            if file_count > 1:
                self.info_label.setText(strings._('gui_file_info', True).format(file_count, total_size_readable))
            else:
                self.info_label.setText(strings._('gui_file_info_single', True).format(file_count, total_size_readable))

        else:
            self.primary_action.hide()
            self.info_widget.hide()

        # Resize window
        self.adjustSize()

    def update_server_status_indicator(self):
        self.common.log('OnionShareGui', 'update_server_status_indicator')

        # Set the status image
        if self.server_status.status == self.server_status.STATUS_STOPPED:
            self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_stopped))
            self.server_status_label.setText(strings._('gui_status_indicator_stopped', True))
        elif self.server_status.status == self.server_status.STATUS_WORKING:
            self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_working))
            self.server_status_label.setText(strings._('gui_status_indicator_working', True))
        elif self.server_status.status == self.server_status.STATUS_STARTED:
            self.server_status_image_label.setPixmap(QtGui.QPixmap.fromImage(self.server_status_image_started))
            self.server_status_label.setText(strings._('gui_status_indicator_started', True))

    def start_server(self):
        """
        Start the onionshare server. This uses multiple threads to start the Tor onion
        server and the web app.
        """
        self.common.log('OnionShareGui', 'start_server')

        self.set_server_active(True)

        self.app.set_stealth(self.common.settings.get('use_stealth'))

        # Hide and reset the downloads if we have previously shared
        self.downloads.reset_downloads()
        self.reset_info_counters()
        self.status_bar.clearMessage()
        self.server_share_status_label.setText('')

        # Reset web counters
        self.web.download_count = 0
        self.web.error404_count = 0

        # start the onion service in a new thread
        def start_onion_service(self):
            try:
                self.app.start_onion_service()
                self.starting_server_step2.emit()

            except (TorTooOld, TorErrorInvalidSetting, TorErrorAutomatic, TorErrorSocketPort, TorErrorSocketFile, TorErrorMissingPassword, TorErrorUnreadableCookieFile, TorErrorAuthError, TorErrorProtocolError, BundledTorTimeout, OSError) as e:
                self.starting_server_error.emit(e.args[0])
                return


            self.app.stay_open = not self.common.settings.get('close_after_first_download')

            # start onionshare http service in new thread
            t = threading.Thread(target=self.web.start, args=(self.app.port, self.app.stay_open, self.common.settings.get('slug')))
            t.daemon = True
            t.start()
            # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
            time.sleep(0.2)

        self.common.log('OnionshareGui', 'start_server', 'Starting an onion thread')
        self.t = OnionThread(self.common, function=start_onion_service, kwargs={'self': self})
        self.t.daemon = True
        self.t.start()

    def start_server_step2(self):
        """
        Step 2 in starting the onionshare server. Zipping up files.
        """
        self.common.log('OnionShareGui', 'start_server_step2')

        # add progress bar to the status bar, indicating the compressing of files.
        self._zip_progress_bar = ZipProgressBar(0)
        self.filenames = []
        for index in range(self.file_selection.file_list.count()):
            self.filenames.append(self.file_selection.file_list.item(index).filename)

        self._zip_progress_bar.total_files_size = ShareMode._compute_total_size(self.filenames)
        self.status_bar.insertWidget(0, self._zip_progress_bar)

        # prepare the files for sending in a new thread
        def finish_starting_server(self):
            # prepare files to share
            def _set_processed_size(x):
                if self._zip_progress_bar != None:
                    self._zip_progress_bar.update_processed_size_signal.emit(x)
            try:
                self.web.set_file_info(self.filenames, processed_size_callback=_set_processed_size)
                self.app.cleanup_filenames.append(self.web.zip_filename)
                self.starting_server_step3.emit()

                # done
                self.start_server_finished.emit()
            except OSError as e:
                self.starting_server_error.emit(e.strerror)
                return

        t = threading.Thread(target=finish_starting_server, kwargs={'self': self})
        t.daemon = True
        t.start()

    def start_server_step3(self):
        """
        Step 3 in starting the onionshare server. This displays the large filesize
        warning, if applicable.
        """
        self.common.log('OnionShareGui', 'start_server_step3')

        # Remove zip progress bar
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None

        # warn about sending large files over Tor
        if self.web.zip_filesize >= 157286400:  # 150mb
            self.filesize_warning.setText(strings._("large_filesize", True))
            self.filesize_warning.show()

        if self.common.settings.get('shutdown_timeout'):
            # Convert the date value to seconds between now and then
            now = QtCore.QDateTime.currentDateTime()
            self.timeout = now.secsTo(self.server_status.timeout)
            # Set the shutdown timeout value
            if self.timeout > 0:
                self.app.shutdown_timer = ShutdownTimer(self.common, self.timeout)
                self.app.shutdown_timer.start()
            # The timeout has actually already passed since the user clicked Start. Probably the Onion service took too long to start.
            else:
                self.stop_server()
                self.start_server_error(strings._('gui_server_started_after_timeout'))

    def start_server_error(self, error):
        """
        If there's an error when trying to start the onion service
        """
        self.common.log('OnionShareGui', 'start_server_error')

        self.set_server_active(False)

        Alert(self.common, error, QtWidgets.QMessageBox.Warning)
        self.server_status.stop_server()
        if self._zip_progress_bar is not None:
            self.status_bar.removeWidget(self._zip_progress_bar)
            self._zip_progress_bar = None
        self.status_bar.clearMessage()

    def cancel_server(self):
        """
        Cancel the server while it is preparing to start
        """
        if self.t:
            self.t.quit()
        self.stop_server()

    def stop_server(self):
        """
        Stop the onionshare server.
        """
        self.common.log('OnionShareGui', 'stop_server')

        if self.server_status.status != self.server_status.STATUS_STOPPED:
            try:
                self.web.stop(self.app.port)
            except:
                # Probably we had no port to begin with (Onion service didn't start)
                pass
        self.app.cleanup()
        # Remove ephemeral service, but don't disconnect from Tor
        self.onion.cleanup(stop_tor=False)
        self.filesize_warning.hide()
        self.downloads_in_progress = 0
        self.downloads_completed = 0
        self.update_downloads_in_progress(0)
        self.file_selection.file_list.adjustSize()

        self.set_server_active(False)
        self.stop_server_finished.emit()

    def downloads_toggled(self, checked):
        """
        When the 'Show/hide downloads' button is toggled, show or hide the downloads window.
        """
        self.common.log('OnionShareGui', 'toggle_downloads')
        if checked:
            self.downloads.downloads_container.show()
        else:
            self.downloads.downloads_container.hide()

    def reset_info_counters(self):
        """
        Set the info counters back to zero.
        """
        self.update_downloads_completed(0)
        self.update_downloads_in_progress(0)
        self.info_show_downloads.setIcon(QtGui.QIcon(self.common.get_resource_path('images/download_window_gray.png')))
        self.downloads.no_downloads_label.show()
        self.downloads.downloads_container.resize(self.downloads.downloads_container.sizeHint())

    def update_downloads_completed(self, count):
        """
        Update the 'Downloads completed' info widget.
        """
        if count == 0:
            self.info_completed_downloads_image = self.common.get_resource_path('images/download_completed_none.png')
        else:
            self.info_completed_downloads_image = self.common.get_resource_path('images/download_completed.png')
        self.info_completed_downloads_count.setText('<img src="{0:s}" /> {1:d}'.format(self.info_completed_downloads_image, count))
        self.info_completed_downloads_count.setToolTip(strings._('info_completed_downloads_tooltip', True).format(count))

    def update_downloads_in_progress(self, count):
        """
        Update the 'Downloads in progress' info widget.
        """
        if count == 0:
            self.info_in_progress_downloads_image = self.common.get_resource_path('images/download_in_progress_none.png')
        else:
            self.info_in_progress_downloads_image = self.common.get_resource_path('images/download_in_progress.png')
            self.info_show_downloads.setIcon(QtGui.QIcon(self.common.get_resource_path('images/download_window_green.png')))
        self.info_in_progress_downloads_count.setText('<img src="{0:s}" /> {1:d}'.format(self.info_in_progress_downloads_image, count))
        self.info_in_progress_downloads_count.setToolTip(strings._('info_in_progress_downloads_tooltip', True).format(count))

    @staticmethod
    def _compute_total_size(filenames):
        total_size = 0
        for filename in filenames:
            if os.path.isfile(filename):
                total_size += os.path.getsize(filename)
            if os.path.isdir(filename):
                total_size += Common.dir_size(filename)
        return total_size
