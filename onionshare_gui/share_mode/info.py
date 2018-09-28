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


class ShareModeInfo(QtWidgets.QWidget):
    """
    Share mode information widget
    """
    def __init__(self, common, share_mode):
        super(ShareModeInfo, self).__init__()
        self.common = common
        self.share_mode = share_mode

        # Label
        self.label_text = ""
        self.label = QtWidgets.QLabel()
        self.label.setStyleSheet(self.common.css['mode_info_label'])

        # In progress and completed labels
        self.in_progress_downloads_count = QtWidgets.QLabel()
        self.in_progress_downloads_count.setStyleSheet(self.common.css['mode_info_label'])
        self.completed_downloads_count = QtWidgets.QLabel()
        self.completed_downloads_count.setStyleSheet(self.common.css['mode_info_label'])

        # Toggle button
        self.toggle_button = QtWidgets.QPushButton()
        self.toggle_button.setDefault(False)
        self.toggle_button.setFixedWidth(30)
        self.toggle_button.setFixedHeight(30)
        self.toggle_button.setFlat(True)
        self.toggle_button.setIcon( QtGui.QIcon(self.common.get_resource_path('images/downloads_toggle.png')) )
        self.toggle_button.clicked.connect(self.toggle_downloads)

        # Info layout
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.in_progress_downloads_count)
        layout.addWidget(self.completed_downloads_count)
        layout.addWidget(self.toggle_button)
        self.setLayout(layout)

        self.update_downloads_completed()
        self.update_downloads_in_progress()

    def update_label(self, s):
        """
        Updates the text of the label.
        """
        self.label_text = s
        self.label.setText(self.label_text)

    def update_downloads_completed(self):
        """
        Update the 'Downloads completed' info widget.
        """
        if self.share_mode.downloads_completed == 0:
            image = self.common.get_resource_path('images/share_completed_none.png')
        else:
            image = self.common.get_resource_path('images/share_completed.png')
        self.completed_downloads_count.setText('<img src="{0:s}" /> {1:d}'.format(image, self.share_mode.downloads_completed))
        self.completed_downloads_count.setToolTip(strings._('info_completed_downloads_tooltip', True).format(self.share_mode.downloads_completed))

    def update_downloads_in_progress(self):
        """
        Update the 'Downloads in progress' info widget.
        """
        if self.share_mode.downloads_in_progress == 0:
            image = self.common.get_resource_path('images/share_in_progress_none.png')
        else:
            image = self.common.get_resource_path('images/share_in_progress.png')
        self.in_progress_downloads_count.setText('<img src="{0:s}" /> {1:d}'.format(image, self.share_mode.downloads_in_progress))
        self.in_progress_downloads_count.setToolTip(strings._('info_in_progress_downloads_tooltip', True).format(self.share_mode.downloads_in_progress))

    def toggle_downloads(self):
        """
        Toggle showing and hiding the Downloads widget
        """
        self.common.log('ShareModeInfo', 'toggle_downloads')

        if self.share_mode.downloads.isVisible():
            self.share_mode.downloads.hide()
            self.toggle_button.setIcon( QtGui.QIcon(self.common.get_resource_path('images/downloads_toggle.png')) )
            self.toggle_button.setFlat(True)
        else:
            self.share_mode.downloads.show()
            self.toggle_button.setIcon( QtGui.QIcon(self.common.get_resource_path('images/downloads_toggle_selected.png')) )
            self.toggle_button.setFlat(False)

        self.share_mode.resize_window()

    def show_less(self):
        """
        Remove clutter widgets that aren't necessary.
        """
        self.label.setText("")

    def show_more(self):
        """
        Show all widgets.
        """
        self.label.setText(self.label_text)
