# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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
import os
import base64
import json

from . import strings
from .gui_common import GuiCommon
from onionshare_cli.meek import MeekNotFound, MeekNotRunning


class MoatDialog(QtWidgets.QDialog):
    """
    Moat dialog: Request a bridge from torproject.org
    """

    got_bridges = QtCore.Signal(str)

    def __init__(self, common, meek):
        super(MoatDialog, self).__init__()

        self.common = common

        self.common.log("MoatDialog", "__init__")

        self.meek = meek

        self.setModal(True)
        self.setWindowTitle(strings._("gui_settings_bridge_moat_button"))
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))

        # Label
        self.label = QtWidgets.QLabel()

        # CAPTCHA image
        self.captcha = QtWidgets.QLabel()
        self.captcha.setFixedSize(400, 125)  # this is the size of the CAPTCHA image

        # Solution input
        self.solution_lineedit = QtWidgets.QLineEdit()
        self.solution_lineedit.setPlaceholderText(strings._("moat_captcha_placeholder"))
        self.solution_lineedit.editingFinished.connect(
            self.solution_lineedit_editing_finished
        )
        self.submit_button = QtWidgets.QPushButton(strings._("moat_captcha_submit"))
        self.submit_button.clicked.connect(self.submit_clicked)
        solution_layout = QtWidgets.QHBoxLayout()
        solution_layout.addWidget(self.solution_lineedit)
        solution_layout.addWidget(self.submit_button)

        # Error label
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet(self.common.gui.css["tor_settings_error"])
        self.error_label.hide()

        # Buttons
        self.reload_button = QtWidgets.QPushButton(strings._("moat_captcha_reload"))
        self.reload_button.clicked.connect(self.reload_clicked)
        self.cancel_button = QtWidgets.QPushButton(
            strings._("gui_settings_button_cancel")
        )
        self.cancel_button.clicked.connect(self.cancel_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.reload_button)
        buttons_layout.addWidget(self.cancel_button)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.captcha)
        layout.addLayout(solution_layout)
        layout.addStretch()
        layout.addWidget(self.error_label)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.cancel_button.setFocus()

        self.reload_clicked()

    def reload_clicked(self):
        """
        Reload button clicked.
        """
        self.common.log("MoatDialog", "reload_clicked")

        self.label.setText(strings._("moat_contact_label"))
        self.error_label.hide()

        self.captcha.hide()
        self.solution_lineedit.hide()
        self.reload_button.hide()
        self.submit_button.hide()

        # BridgeDB fetch
        self.t_fetch = MoatThread(self.common, self.meek, "fetch")
        self.t_fetch.bridgedb_error.connect(self.bridgedb_error)
        self.t_fetch.captcha_ready.connect(self.captcha_ready)
        self.t_fetch.start()

    def submit_clicked(self):
        """
        Submit button clicked.
        """
        self.error_label.hide()
        self.solution_lineedit.setEnabled(False)

        solution = self.solution_lineedit.text().strip()
        if len(solution) == 0:
            self.common.log("MoatDialog", "submit_clicked", "solution is blank")
            self.error_label.setText(strings._("moat_solution_empty_error"))
            self.error_label.show()
            return

        # BridgeDB check
        self.t_check = MoatThread(
            self.common,
            self.meek,
            "check",
            {
                "transport": self.transport,
                "challenge": self.challenge,
                "solution": self.solution_lineedit.text(),
            },
        )
        self.t_check.bridgedb_error.connect(self.bridgedb_error)
        self.t_check.captcha_error.connect(self.captcha_error)
        self.t_check.bridges_ready.connect(self.bridges_ready)
        self.t_check.start()

    def cancel_clicked(self):
        """
        Cancel button clicked.
        """
        self.common.log("MoatDialog", "cancel_clicked")
        self.close()

    def bridgedb_error(self):
        self.common.log("MoatDialog", "bridgedb_error")
        self.error_label.setText(strings._("moat_bridgedb_error"))
        self.error_label.show()

        self.solution_lineedit.setEnabled(True)

    def captcha_error(self, msg):
        self.common.log("MoatDialog", "captcha_error")
        if msg == "":
            self.error_label.setText(strings._("moat_captcha_error"))
        else:
            self.error_label.setText(msg)
        self.error_label.show()

        self.solution_lineedit.setEnabled(True)

    def captcha_ready(self, transport, image, challenge):
        self.common.log("MoatDialog", "captcha_ready")

        self.transport = transport
        self.challenge = challenge

        # Save captcha image to disk, so we can load it
        captcha_data = base64.b64decode(image)
        captcha_filename = os.path.join(self.common.build_tmp_dir(), "captcha.jpg")
        with open(captcha_filename, "wb") as f:
            f.write(captcha_data)

        self.captcha.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(captcha_filename)))
        os.remove(captcha_filename)

        self.label.setText(strings._("moat_captcha_label"))
        self.captcha.show()
        self.solution_lineedit.setEnabled(True)
        self.solution_lineedit.setText("")
        self.solution_lineedit.show()
        self.solution_lineedit.setFocus()
        self.reload_button.show()
        self.submit_button.show()

    def solution_lineedit_editing_finished(self):
        self.common.log("MoatDialog", "solution_lineedit_editing_finished")

    def bridges_ready(self, bridges):
        self.common.log("MoatDialog", "bridges_ready", bridges)
        self.got_bridges.emit(bridges)
        self.close()


class MoatThread(QtCore.QThread):
    """
    This does all of the communicating with BridgeDB in a separate thread.

    Valid actions are:
    - "fetch": requests a new CAPTCHA
    - "check": sends a CAPTCHA solution

    """

    bridgedb_error = QtCore.Signal()
    captcha_error = QtCore.Signal(str)
    captcha_ready = QtCore.Signal(str, str, str)
    bridges_ready = QtCore.Signal(str)

    def __init__(self, common, meek, action, data={}):
        super(MoatThread, self).__init__()
        self.common = common
        self.common.log("MoatThread", "__init__", f"action={action}")

        self.meek = meek
        self.transport = "obfs4"
        self.action = action
        self.data = data

    def run(self):

        # Start Meek so that we can do domain fronting
        try:
            self.meek.start()
        except (
            MeekNotFound,
            MeekNotRunning,
        ):
            self.bridgedb_error.emit()
            return

        # We should only fetch bridges if we can domain front,
        # but we can override this in local-only mode.
        if not self.meek.meek_proxies and not self.common.gui.local_only:
            self.common.log(
                "MoatThread", "run", f"Could not identify meek proxies to make request"
            )
            self.bridgedb_error.emit()
            return

        if self.action == "fetch":
            self.common.log("MoatThread", "run", f"starting fetch")

            # Request a bridge
            r = requests.post(
                "https://bridges.torproject.org/moat/fetch",
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.meek.meek_proxies,
                json={
                    "data": [
                        {
                            "version": "0.1.0",
                            "type": "client-transports",
                            "supported": ["obfs4", "snowflake"],
                        }
                    ]
                },
            )

            self.meek.cleanup()

            if r.status_code != 200:
                self.common.log("MoatThread", "run", f"status_code={r.status_code}")
                self.bridgedb_error.emit()
                return

            try:
                moat_res = r.json()
                if "errors" in moat_res:
                    self.common.log("MoatThread", "run", f"errors={moat_res['errors']}")
                    self.bridgedb_error.emit()
                    return
                if "data" not in moat_res:
                    self.common.log("MoatThread", "run", f"no data")
                    self.bridgedb_error.emit()
                    return
                if moat_res["data"][0]["type"] != "moat-challenge":
                    self.common.log("MoatThread", "run", f"type != moat-challange")
                    self.bridgedb_error.emit()
                    return

                transport = moat_res["data"][0]["transport"]
                image = moat_res["data"][0]["image"]
                challenge = moat_res["data"][0]["challenge"]

                self.captcha_ready.emit(transport, image, challenge)
            except Exception as e:
                self.common.log("MoatThread", "run", f"hit exception: {e}")
                self.bridgedb_error.emit()
                return

        elif self.action == "check":
            self.common.log("MoatThread", "run", f"starting check")

            # Check the CAPTCHA
            r = requests.post(
                "https://bridges.torproject.org/moat/check",
                headers={"Content-Type": "application/vnd.api+json"},
                proxies=self.meek.meek_proxies,
                json={
                    "data": [
                        {
                            "id": "2",
                            "type": "moat-solution",
                            "version": "0.1.0",
                            "transport": self.data["transport"],
                            "challenge": self.data["challenge"],
                            "solution": self.data["solution"],
                            "qrcode": "false",
                        }
                    ]
                },
            )

            self.meek.cleanup()

            if r.status_code != 200:
                self.common.log("MoatThread", "run", f"status_code={r.status_code}")
                self.bridgedb_error.emit()
                return

            try:
                moat_res = r.json()
                self.common.log(
                    "MoatThread",
                    "run",
                    f"got bridges:\n{json.dumps(moat_res,indent=2)}",
                )

                if "errors" in moat_res:
                    self.common.log("MoatThread", "run", f"errors={moat_res['errors']}")
                    if moat_res["errors"][0]["code"] == 419:
                        self.captcha_error.emit("")
                        return
                    else:
                        errors = " ".join([e["detail"] for e in moat_res["errors"]])
                        self.captcha_error.emit(errors)
                        return

                if moat_res["data"][0]["type"] != "moat-bridges":
                    self.common.log("MoatThread", "run", f"type != moat-bridges")
                    self.bridgedb_error.emit()
                    return

                bridges = moat_res["data"][0]["bridges"]
                self.bridges_ready.emit("\n".join(bridges))

            except Exception as e:
                self.common.log("MoatThread", "run", f"hit exception: {e}")
                self.bridgedb_error.emit()
                return

        else:
            self.common.log("MoatThread", "run", f"invalid action: {self.action}")
