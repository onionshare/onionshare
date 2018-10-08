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
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings


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


class DownloadHistoryItem(HistoryItem):
    """
    Download history item, for share mode
    """
    def __init__(self, common, id, total_bytes):
        super(DownloadHistoryItem, self).__init__()
        self.common = common

        self.id = id
        self.started = time.time()
        self.total_bytes = total_bytes
        self.downloaded_bytes = 0

        self.setStyleSheet('QWidget { border: 1px solid red; }')

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
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        # Start at 0
        self.update(0)

    def update(self, downloaded_bytes):
        self.downloaded_bytes = downloaded_bytes

        self.progress_bar.setValue(downloaded_bytes)
        if downloaded_bytes == self.progress_bar.total_bytes:
            pb_fmt = strings._('gui_download_upload_progress_complete').format(
                self.common.format_seconds(time.time() - self.started))
        else:
            elapsed = time.time() - self.started
            if elapsed < 10:
                # Wait a couple of seconds for the download rate to stabilize.
                # This prevents a "Windows copy dialog"-esque experience at
                # the beginning of the download.
                pb_fmt = strings._('gui_download_upload_progress_starting').format(
                    self.common.human_readable_filesize(downloaded_bytes))
            else:
                pb_fmt = strings._('gui_download_upload_progress_eta').format(
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
        self.items[id].update(data)

    def cancel(self, id):
        """
        Cancel an item.  Override this method.
        """
        self.items[id].cancel()

    def reset(self):
        """
        Reset all items, emptying the list.  Override this method.
        """
        for item in self.items.values():
            self.items_layout.removeWidget(item)
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

        # Header
        self.header_label = QtWidgets.QLabel(header_text)
        self.header_label.setStyleSheet(self.common.css['downloads_uploads_label'])
        clear_button = QtWidgets.QPushButton(strings._('gui_clear_history', True))
        clear_button.setStyleSheet(self.common.css['downloads_uploads_clear'])
        clear_button.setFlat(True)
        clear_button.clicked.connect(self.reset)
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_button)

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

        self.current_mode.resize_window()
