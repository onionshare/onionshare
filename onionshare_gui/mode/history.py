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
import time
import subprocess
import os
from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings
from ..widgets import Alert


class HistoryItem(QtWidgets.QWidget):
    """
    The base history item
    """
    def __init__(self):
        super(HistoryItem, self).__init__()

    def update(self):
        pass

    def cancel(self):
        pass

    def get_finished_label_text(self, started):
        """
        When an item finishes, returns a string displaying the start/end datetime range.
        started is a datetime object.
        """
        return self._get_label_text('gui_all_modes_transfer_finished', 'gui_all_modes_transfer_finished_range', started)

    def get_canceled_label_text(self, started):
        """
        When an item is canceled, returns a string displaying the start/end datetime range.
        started is a datetime object.
        """
        return self._get_label_text('gui_all_modes_transfer_canceled', 'gui_all_modes_transfer_canceled_range', started)

    def _get_label_text(self, string_name, string_range_name, started):
        """
        Return a string that contains a date, or date range.
        """
        ended = datetime.now()
        if started.year == ended.year and started.month == ended.month and started.day == ended.day:
            if started.hour == ended.hour and started.minute == ended.minute:
                text = strings._(string_name).format(
                    started.strftime("%b %d, %I:%M%p")
                )
            else:
                text = strings._(string_range_name).format(
                    started.strftime("%b %d, %I:%M%p"),
                    ended.strftime("%I:%M%p")
                )
        else:
            text = strings._(string_range_name).format(
                started.strftime("%b %d, %I:%M%p"),
                ended.strftime("%b %d, %I:%M%p")
            )
        return text


class ShareHistoryItem(HistoryItem):
    """
    Download history item, for share mode
    """
    def __init__(self, common, id, total_bytes):
        super(ShareHistoryItem, self).__init__()
        self.common = common

        self.id = id
        self.total_bytes = total_bytes
        self.downloaded_bytes = 0
        self.started = time.time()
        self.started_dt = datetime.fromtimestamp(self.started)

        # Label
        self.label = QtWidgets.QLabel(strings._('gui_all_modes_transfer_started').format(self.started_dt.strftime("%b %d, %I:%M%p")))

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.progress_bar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(total_bytes)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(self.common.css['downloads_uploads_progress_bar'])
        self.progress_bar.total_bytes = total_bytes

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        # Start at 0
        self.update(0)

    def update(self, downloaded_bytes):
        self.downloaded_bytes = downloaded_bytes

        self.progress_bar.setValue(downloaded_bytes)
        if downloaded_bytes == self.progress_bar.total_bytes:
            pb_fmt = strings._('gui_all_modes_progress_complete').format(
                self.common.format_seconds(time.time() - self.started))

            # Change the label
            self.label.setText(self.get_finished_label_text(self.started_dt))

        else:
            elapsed = time.time() - self.started
            if elapsed < 10:
                # Wait a couple of seconds for the download rate to stabilize.
                # This prevents a "Windows copy dialog"-esque experience at
                # the beginning of the download.
                pb_fmt = strings._('gui_all_modes_progress_starting').format(
                    self.common.human_readable_filesize(downloaded_bytes))
            else:
                pb_fmt = strings._('gui_all_modes_progress_eta').format(
                    self.common.human_readable_filesize(downloaded_bytes),
                    self.estimated_time_remaining)

        self.progress_bar.setFormat(pb_fmt)

    def cancel(self):
        self.progress_bar.setFormat(strings._('gui_canceled'))

    @property
    def estimated_time_remaining(self):
        return self.common.estimated_time_remaining(self.downloaded_bytes,
                                                self.total_bytes,
                                                self.started)


class ReceiveHistoryItemFile(QtWidgets.QWidget):
    def __init__(self, common, filename):
        super(ReceiveHistoryItemFile, self).__init__()
        self.common = common

        self.common.log('ReceiveHistoryItemFile', '__init__', 'filename: {}'.format(filename))

        self.filename = filename
        self.dir = None
        self.started = datetime.now()

        # Filename label
        self.filename_label = QtWidgets.QLabel(self.filename)
        self.filename_label_width = self.filename_label.width()

        # File size label
        self.filesize_label = QtWidgets.QLabel()
        self.filesize_label.setStyleSheet(self.common.css['receive_file_size'])
        self.filesize_label.hide()

        # Folder button
        folder_pixmap = QtGui.QPixmap.fromImage(QtGui.QImage(self.common.get_resource_path('images/open_folder.png')))
        folder_icon = QtGui.QIcon(folder_pixmap)
        self.folder_button = QtWidgets.QPushButton()
        self.folder_button.clicked.connect(self.open_folder)
        self.folder_button.setIcon(folder_icon)
        self.folder_button.setIconSize(folder_pixmap.rect().size())
        self.folder_button.setFlat(True)
        self.folder_button.hide()

        # Layouts
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.filename_label)
        layout.addWidget(self.filesize_label)
        layout.addStretch()
        layout.addWidget(self.folder_button)
        self.setLayout(layout)

    def update(self, uploaded_bytes, complete):
        self.filesize_label.setText(self.common.human_readable_filesize(uploaded_bytes))
        self.filesize_label.show()

        if complete:
            self.folder_button.show()

    def rename(self, new_filename):
        self.filename = new_filename
        self.filename_label.setText(self.filename)

    def set_dir(self, dir):
        self.dir = dir

    def open_folder(self):
        """
        Open the downloads folder, with the file selected, in a cross-platform manner
        """
        self.common.log('ReceiveHistoryItemFile', 'open_folder')

        if not self.dir:
            self.common.log('ReceiveHistoryItemFile', 'open_folder', "dir has not been set yet, can't open folder")
            return

        abs_filename = os.path.join(self.dir, self.filename)

        # Linux
        if self.common.platform == 'Linux' or self.common.platform == 'BSD':
            try:
                # If nautilus is available, open it
                subprocess.Popen(['nautilus', abs_filename])
            except:
                Alert(self.common, strings._('gui_open_folder_error_nautilus').format(abs_filename))

        # macOS
        elif self.common.platform == 'Darwin':
            subprocess.call(['open', '-R', abs_filename])

        # Windows
        elif self.common.platform == 'Windows':
            subprocess.Popen(['explorer', '/select,{}'.format(abs_filename)])

class ReceiveHistoryItem(HistoryItem):
    def __init__(self, common, id, content_length):
        super(ReceiveHistoryItem, self).__init__()
        self.common = common
        self.id = id
        self.content_length = content_length
        self.started = datetime.now()

        # Label
        self.label = QtWidgets.QLabel(strings._('gui_all_modes_transfer_started').format(self.started.strftime("%b %d, %I:%M%p")))

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.progress_bar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(self.common.css['downloads_uploads_progress_bar'])

        # This layout contains file widgets
        self.files_layout = QtWidgets.QVBoxLayout()
        self.files_layout.setContentsMargins(0, 0, 0, 0)
        files_widget = QtWidgets.QWidget()
        files_widget.setStyleSheet(self.common.css['receive_file'])
        files_widget.setLayout(self.files_layout)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(files_widget)
        layout.addStretch()
        self.setLayout(layout)

        # We're also making a dictionary of file widgets, to make them easier to access
        self.files = {}

    def update(self, data):
        """
        Using the progress from Web, update the progress bar and file size labels
        for each file
        """
        if data['action'] == 'progress':
            total_uploaded_bytes = 0
            for filename in data['progress']:
                total_uploaded_bytes += data['progress'][filename]['uploaded_bytes']

            # Update the progress bar
            self.progress_bar.setMaximum(self.content_length)
            self.progress_bar.setValue(total_uploaded_bytes)

            elapsed = datetime.now() - self.started
            if elapsed.seconds < 10:
                pb_fmt = strings._('gui_all_modes_progress_starting').format(
                    self.common.human_readable_filesize(total_uploaded_bytes))
            else:
                estimated_time_remaining = self.common.estimated_time_remaining(
                    total_uploaded_bytes,
                    self.content_length,
                    self.started.timestamp())
                pb_fmt = strings._('gui_all_modes_progress_eta').format(
                    self.common.human_readable_filesize(total_uploaded_bytes),
                    estimated_time_remaining)

            # Using list(progress) to avoid "RuntimeError: dictionary changed size during iteration"
            for filename in list(data['progress']):
                # Add a new file if needed
                if filename not in self.files:
                    self.files[filename] = ReceiveHistoryItemFile(self.common, filename)
                    self.files_layout.addWidget(self.files[filename])

                # Update the file
                self.files[filename].update(data['progress'][filename]['uploaded_bytes'], data['progress'][filename]['complete'])

        elif data['action'] == 'rename':
            self.files[data['old_filename']].rename(data['new_filename'])
            self.files[data['new_filename']] = self.files.pop(data['old_filename'])

        elif data['action'] == 'set_dir':
            self.files[data['filename']].set_dir(data['dir'])

        elif data['action'] == 'finished':
            # Hide the progress bar
            self.progress_bar.hide()

            # Change the label
            self.label.setText(self.get_finished_label_text(self.started))

        elif data['action'] == 'canceled':
            # Hide the progress bar
            self.progress_bar.hide()

            # Change the label
            self.label.setText(self.get_canceled_label_text(self.started))


class HistoryItemList(QtWidgets.QScrollArea):
    """
    List of items
    """
    def __init__(self, common):
        super(HistoryItemList, self).__init__()
        self.common = common

        self.items = {}

        # The layout that holds all of the items
        self.items_layout = QtWidgets.QVBoxLayout()
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        # Wrapper layout that also contains a stretch
        wrapper_layout = QtWidgets.QVBoxLayout()
        wrapper_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
        wrapper_layout.addLayout(self.items_layout)
        wrapper_layout.addStretch()

        # The internal widget of the scroll area
        widget = QtWidgets.QWidget()
        widget.setLayout(wrapper_layout)
        self.setWidget(widget)
        self.setWidgetResizable(True)

        # Other scroll area settings
        self.setBackgroundRole(QtGui.QPalette.Light)
        self.verticalScrollBar().rangeChanged.connect(self.resizeScroll)

    def resizeScroll(self, minimum, maximum):
        """
        Scroll to the bottom of the window when the range changes.
        """
        self.verticalScrollBar().setValue(maximum)

    def add(self, id, item):
        """
        Add a new item. Override this method.
        """
        self.items[id] = item
        self.items_layout.addWidget(item)

    def update(self, id, data):
        """
        Update an item.  Override this method.
        """
        if id in self.items:
            self.items[id].update(data)

    def cancel(self, id):
        """
        Cancel an item.  Override this method.
        """
        if id in self.items:
            self.items[id].cancel()

    def reset(self):
        """
        Reset all items, emptying the list.  Override this method.
        """
        for item in self.items.values():
            self.items_layout.removeWidget(item)
            item.close()
        self.items = {}


class History(QtWidgets.QWidget):
    """
    A history of what's happened so far in this mode. This contains an internal
    object full of a scrollable list of items.
    """
    def __init__(self, common, empty_image, empty_text, header_text):
        super(History, self).__init__()
        self.common = common

        self.setMinimumWidth(350)

        # In progress and completed counters
        self.in_progress_count = 0
        self.completed_count = 0

        # In progress and completed labels
        self.in_progress_label = QtWidgets.QLabel()
        self.in_progress_label.setStyleSheet(self.common.css['mode_info_label'])
        self.completed_label = QtWidgets.QLabel()
        self.completed_label.setStyleSheet(self.common.css['mode_info_label'])

        # Header
        self.header_label = QtWidgets.QLabel(header_text)
        self.header_label.setStyleSheet(self.common.css['downloads_uploads_label'])
        clear_button = QtWidgets.QPushButton(strings._('gui_all_modes_clear_history'))
        clear_button.setStyleSheet(self.common.css['downloads_uploads_clear'])
        clear_button.setFlat(True)
        clear_button.clicked.connect(self.reset)
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.in_progress_label)
        header_layout.addWidget(self.completed_label)
        header_layout.addWidget(clear_button)

        # When there are no items
        self.empty_image = QtWidgets.QLabel()
        self.empty_image.setAlignment(QtCore.Qt.AlignCenter)
        self.empty_image.setPixmap(empty_image)
        self.empty_text = QtWidgets.QLabel(empty_text)
        self.empty_text.setAlignment(QtCore.Qt.AlignCenter)
        self.empty_text.setStyleSheet(self.common.css['downloads_uploads_empty_text'])
        empty_layout = QtWidgets.QVBoxLayout()
        empty_layout.addStretch()
        empty_layout.addWidget(self.empty_image)
        empty_layout.addWidget(self.empty_text)
        empty_layout.addStretch()
        self.empty = QtWidgets.QWidget()
        self.empty.setStyleSheet(self.common.css['downloads_uploads_empty'])
        self.empty.setLayout(empty_layout)

        # When there are items
        self.item_list = HistoryItemList(self.common)
        self.not_empty_layout = QtWidgets.QVBoxLayout()
        self.not_empty_layout.addLayout(header_layout)
        self.not_empty_layout.addWidget(self.item_list)
        self.not_empty = QtWidgets.QWidget()
        self.not_empty.setLayout(self.not_empty_layout)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.empty)
        layout.addWidget(self.not_empty)
        self.setLayout(layout)

        # Reset once at the beginning
        self.reset()

    def add(self, id, item):
        """
        Add a new item.
        """
        self.common.log('History', 'add', 'id: {}, item: {}'.format(id, item))

        # Hide empty, show not empty
        self.empty.hide()
        self.not_empty.show()

        # Add it to the list
        self.item_list.add(id, item)

    def update(self, id, data):
        """
        Update an item.
        """
        self.item_list.update(id, data)

    def cancel(self, id):
        """
        Cancel an item.
        """
        self.item_list.cancel(id)

    def reset(self):
        """
        Reset all items.
        """
        self.item_list.reset()

        # Hide not empty, show empty
        self.not_empty.hide()
        self.empty.show()

        # Reset counters
        self.completed_count = 0
        self.in_progress_count = 0
        self.update_completed()
        self.update_in_progress()

    def update_completed(self):
        """
        Update the 'completed' widget.
        """
        if self.completed_count == 0:
            image = self.common.get_resource_path('images/share_completed_none.png')
        else:
            image = self.common.get_resource_path('images/share_completed.png')
        self.completed_label.setText('<img src="{0:s}" /> {1:d}'.format(image, self.completed_count))
        self.completed_label.setToolTip(strings._('history_completed_tooltip').format(self.completed_count))

    def update_in_progress(self):
        """
        Update the 'in progress' widget.
        """
        if self.in_progress_count == 0:
            image = self.common.get_resource_path('images/share_in_progress_none.png')
        else:
            image = self.common.get_resource_path('images/share_in_progress.png')
        self.in_progress_label.setText('<img src="{0:s}" /> {1:d}'.format(image, self.in_progress_count))
        self.in_progress_label.setToolTip(strings._('history_in_progress_tooltip').format(self.in_progress_count))


class ToggleHistory(QtWidgets.QPushButton):
    """
    Widget for toggling showing or hiding the history, as well as keeping track
    of the indicator counter if it's hidden
    """
    def __init__(self, common, current_mode, history_widget, icon, selected_icon):
        super(ToggleHistory, self).__init__()
        self.common = common
        self.current_mode = current_mode
        self.history_widget = history_widget
        self.icon = icon
        self.selected_icon = selected_icon

        # Toggle button
        self.setDefault(False)
        self.setFixedWidth(35)
        self.setFixedHeight(30)
        self.setFlat(True)
        self.setIcon(icon)
        self.clicked.connect(self.toggle_clicked)

        # Keep track of indicator
        self.indicator_count = 0
        self.indicator_label = QtWidgets.QLabel(parent=self)
        self.indicator_label.setStyleSheet(self.common.css['download_uploads_indicator'])
        self.update_indicator()

    def update_indicator(self, increment=False):
        """
        Update the display of the indicator count. If increment is True, then
        only increment the counter if Downloads is hidden.
        """
        if increment and not self.history_widget.isVisible():
            self.indicator_count += 1

        self.indicator_label.setText("{}".format(self.indicator_count))

        if self.indicator_count == 0:
            self.indicator_label.hide()
        else:
            size = self.indicator_label.sizeHint()
            self.indicator_label.setGeometry(35-size.width(), 0, size.width(), size.height())
            self.indicator_label.show()

    def toggle_clicked(self):
        """
        Toggle showing and hiding the history widget
        """
        self.common.log('ToggleHistory', 'toggle_clicked')

        if self.history_widget.isVisible():
            self.history_widget.hide()
            self.setIcon(self.icon)
            self.setFlat(True)
        else:
            self.history_widget.show()
            self.setIcon(self.selected_icon)
            self.setFlat(False)

        # Reset the indicator count
        self.indicator_count = 0
        self.update_indicator()
