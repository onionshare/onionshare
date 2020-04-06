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
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from PyQt5 import QtCore


class EventHandler(FileSystemEventHandler, QtCore.QObject):
    """
    To trigger an event, write a JSON line to the events file. When that file changes, 
    each line will be handled as an event. Valid events are:
    {"type": "new_tab"}
    {"type": "new_share_tab", "filenames": ["file1", "file2"]}
    """

    new_tab = QtCore.pyqtSignal()
    new_share_tab = QtCore.pyqtSignal(list)

    def __init__(self, common):
        super(EventHandler, self).__init__()
        self.common = common

    def on_modified(self, event):
        if (
            type(event) == FileModifiedEvent
            and event.src_path == self.common.gui.events_filename
        ):
            # Read all the lines in the events, then delete it
            with open(self.common.gui.events_filename, "r") as f:
                lines = f.readlines()
            os.remove(self.common.gui.events_filename)

            self.common.log(
                "EventHandler", "on_modified", f"processing {len(lines)} lines"
            )
            for line in lines:
                try:
                    obj = json.loads(line)
                    if "type" not in obj:
                        self.common.log(
                            "EventHandler",
                            "on_modified",
                            f"event does not have a type: {obj}",
                        )
                        continue
                except json.decoder.JSONDecodeError:
                    self.common.log(
                        "EventHandler", "on_modified", f"ignoring invalid line: {line}"
                    )
                    continue

                if obj["type"] == "new_tab":
                    self.common.log("EventHandler", "on_modified", "new_tab event")
                    self.new_tab.emit()

                elif obj["type"] == "new_share_tab":
                    if "filenames" in obj and type(obj["filenames"]) is list:
                        self.new_share_tab.emit(obj["filenames"])
                    else:
                        self.common.log(
                            "EventHandler",
                            "on_modified",
                            f"invalid new_share_tab event: {obj}",
                        )

                else:
                    self.common.log(
                        "EventHandler", "on_modified", f"invalid event type: {obj}"
                    )

