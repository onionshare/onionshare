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


class ReceiveModeInfo(QtWidgets.QWidget):
    """
    Receive mode information widget
    """
    def __init__(self, common, receive_mode):
        super(ReceiveModeInfo, self).__init__()
        self.common = common
        self.receive_mode = receive_mode

        # In progress and completed labels
        self.in_progress_uploads_count = QtWidgets.QLabel()
        self.in_progress_uploads_count.setStyleSheet(self.common.css['mode_info_label'])
        self.completed_uploads_count = QtWidgets.QLabel()
        self.completed_uploads_count.setStyleSheet(self.common.css['mode_info_label'])

        # Toggle button
        self.toggle_button = QtWidgets.QPushButton()
        self.toggle_button.setDefault(False)
        self.toggle_button.setFixedWidth(30)
        self.toggle_button.setFixedHeight(30)
        self.toggle_button.setFlat(True)
        self.toggle_button.setIcon( QtGui.QIcon(self.common.get_resource_path('images/uploads_toggle.png')) )
        self.toggle_button.clicked.connect(self.toggle_uploads)

        # Keep track of indicator
        self.indicator_count = 0
        self.indicator_label = QtWidgets.QLabel()
        self.indicator_label.setStyleSheet(self.common.css['download_uploads_indicator'])
        self.update_indicator()

        # Layout
        layout = QtWidgets.QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.in_progress_uploads_count)
        layout.addWidget(self.completed_uploads_count)
        layout.addWidget(self.indicator_label)
        layout.addWidget(self.toggle_button)
        self.setLayout(layout)

        self.update_uploads_completed()
        self.update_uploads_in_progress()

    def update_indicator(self, increment=False):
        """
        Update the display of the indicator count. If increment is True, then
        only increment the counter if Uploads is hidden.
        """
        if increment and not self.receive_mode.uploads.isVisible():
            self.indicator_count += 1

        self.indicator_label.setText("{}".format(self.indicator_count))

        if self.indicator_count == 0:
            self.indicator_label.hide()
        else:
            self.indicator_label.show()

    def update_uploads_completed(self):
        """
        Update the 'Uploads completed' info widget.
        """
        if self.receive_mode.uploads_completed == 0:
            image = self.common.get_resource_path('images/share_completed_none.png')
        else:
            image = self.common.get_resource_path('images/share_completed.png')
        self.completed_uploads_count.setText('<img src="{0:s}" /> {1:d}'.format(image, self.receive_mode.uploads_completed))
        self.completed_uploads_count.setToolTip(strings._('info_completed_uploads_tooltip', True).format(self.receive_mode.uploads_completed))

    def update_uploads_in_progress(self):
        """
        Update the 'Uploads in progress' info widget.
        """
        if self.receive_mode.uploads_in_progress == 0:
            image = self.common.get_resource_path('images/share_in_progress_none.png')
        else:
            image = self.common.get_resource_path('images/share_in_progress.png')
        self.in_progress_uploads_count.setText('<img src="{0:s}" /> {1:d}'.format(image, self.receive_mode.uploads_in_progress))
        self.in_progress_uploads_count.setToolTip(strings._('info_in_progress_uploads_tooltip', True).format(self.receive_mode.uploads_in_progress))

    def toggle_uploads(self):
        """
        Toggle showing and hiding the Uploads widget
        """
        self.common.log('ReceiveModeInfo', 'toggle_uploads')

        if self.receive_mode.uploads.isVisible():
            self.receive_mode.uploads.hide()
            self.toggle_button.setIcon( QtGui.QIcon(self.common.get_resource_path('images/uploads_toggle.png')) )
            self.toggle_button.setFlat(True)
        else:
            self.receive_mode.uploads.show()
            self.toggle_button.setIcon( QtGui.QIcon(self.common.get_resource_path('images/uploads_toggle_selected.png')) )
            self.toggle_button.setFlat(False)

        # Reset the indicator count
        self.indicator_count = 0
        self.update_indicator()

        self.receive_mode.resize_window()

    def show_less(self):
        """
        Remove clutter widgets that aren't necessary.
        """
        pass

    def show_more(self):
        """
        Show all widgets.
        """
        pass
