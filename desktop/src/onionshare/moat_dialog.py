# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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

from PySide2 import QtCore, QtWidgets, QtGui
import requests

from . import strings
from .gui_common import GuiCommon


class MoatDialog(QtWidgets.QDialog):
    """
    Moat dialog: Request a bridge from torproject.org
    """

    def __init__(self, common):
        super(MoatDialog, self).__init__()

        self.common = common

        self.common.log("MoatDialog", "__init__")

        self.setModal(True)
        self.setWindowTitle(strings._("gui_settings_bridge_moat_button"))
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))

        # Label
        self.label = QtWidgets.QLabel(strings._("moat_contact_label"))

        # CAPTCHA image
        self.captcha = QtWidgets.QLabel()
        self.captcha.setFixedSize(400, 125)  # this is the size of the CAPTCHA image

        # Solution input
        self.solution_lineedit = QtWidgets.QLineEdit()
        self.solution_lineedit.editingFinished.connect(self.solution_editing_finished)
        self.reload_button = QtWidgets.QPushButton(strings._("moat_captcha_reload"))
        self.reload_button.clicked.connect(self.reload_clicked)
        solution_layout = QtWidgets.QHBoxLayout()
        solution_layout.addWidget(self.solution_lineedit)
        solution_layout.addWidget(self.reload_button)

        # Error label
        self.error_label = QtWidgets.QLabel()
        self.error_label.hide()

        # Buttons
        self.submit_button = QtWidgets.QPushButton(strings._("moat_captcha_submit"))
        self.submit_button.clicked.connect(self.submit_clicked)
        self.submit_button.setEnabled(False)
        self.cancel_button = QtWidgets.QPushButton(
            strings._("gui_settings_button_cancel")
        )
        self.cancel_button.clicked.connect(self.cancel_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.submit_button)
        buttons_layout.addWidget(self.cancel_button)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.captcha)
        layout.addLayout(solution_layout)
        layout.addWidget(self.error_label)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.cancel_button.setFocus()

        self.reload_clicked()
        self.exec_()

    def solution_editing_finished(self):
        """
        Finished typing something in the solution field.
        """
        self.common.log("MoatDialog", "solution_editing_finished")
        pass

    def reload_clicked(self):
        """
        Reload button clicked.
        """
        self.common.log("MoatDialog", "reload_clicked")
        pass

    def submit_clicked(self):
        """
        Submit button clicked.
        """
        self.common.log("MoatDialog", "submit_clicked")
        pass

    def cancel_clicked(self):
        """
        Cancel button clicked.
        """
        self.common.log("MoatDialog", "cancel_clicked")
        pass


class MoatThread(QtCore.QThread):
    """
    This does all of the communicating with BridgeDB in a separate thread.

    Valid actions are:
    - "fetch": requests a new CAPTCHA
    - "check": sends a CAPTCHA solution

    """

    tor_status_update = QtCore.Signal(str, str)

    def __init__(self, common, action, data):
        super(MoatThread, self).__init__()
        self.common = common
        self.common.log("MoatThread", "__init__", f"action={action}")

        self.action = action
        self.data = data

    def run(self):
        self.common.log("MoatThread", "run")

        # TODO: Do all of this using domain fronting

        # Request a bridge
        r = requests.post(
            "https://bridges.torproject.org/moat/fetch",
            headers={"Content-Type": "application/vnd.api+json"},
            json={
                "data": [
                    {
                        "version": "0.1.0",
                        "type": "client-transports",
                        "supported": ["obfs4"],
                    }
                ]
            },
        )
        if r.status_code != 200:
            return moat_error()

        try:
            moat_res = r.json()
            if "errors" in moat_res or "data" not in moat_res:
                return moat_error()
            if moat_res["type"] != "moat-challenge":
                return moat_error()

            moat_type = moat_res["type"]
            moat_transport = moat_res["transport"]
            moat_image = moat_res["image"]
            moat_challenge = moat_res["challenge"]
        except:
            return moat_error()
