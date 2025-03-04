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

import json
import os
import requests
import time
from datetime import datetime
from PySide6 import QtCore

from onionshare_cli.onion import (
    TorErrorInvalidSetting,
    TorErrorAutomatic,
    TorErrorSocketPort,
    TorErrorSocketFile,
    TorErrorMissingPassword,
    TorErrorUnreadableCookieFile,
    TorErrorAuthError,
    TorErrorProtocolError,
    BundledTorTimeout,
    BundledTorBroken,
    TorTooOldEphemeral,
    TorTooOldStealth,
    PortNotAvailable,
)

from onionshare_cli.web.web import WaitressException

from . import strings


class OnionThread(QtCore.QThread):
    """
    Starts the onion service, and waits for it to finish
    """

    success = QtCore.Signal()
    success_early = QtCore.Signal()
    error = QtCore.Signal(str)

    def __init__(self, mode):
        super(OnionThread, self).__init__()
        self.mode = mode
        self.mode.common.log("OnionThread", "__init__")

        # allow this thread to be terminated
        self.setTerminationEnabled()

    def run(self):
        self.mode.common.log("OnionThread", "run")

        # Choose port early, because we need them to exist in advance for scheduled shares
        if not self.mode.app.port:
            self.mode.app.choose_port()

        try:
            if self.mode.obtain_onion_early:
                self.mode.app.start_onion_service(
                    self.mode.get_type(), self.mode.settings, await_publication=False
                )
                # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
                time.sleep(0.2)
                self.success_early.emit()
                # Unregister the onion so we can use it in the next OnionThread
                self.mode.app.stop_onion_service(self.mode.settings)
            else:
                self.mode.app.start_onion_service(
                    self.mode.get_type(), self.mode.settings, await_publication=True
                )
                # wait for modules in thread to load, preventing a thread-related cx_Freeze crash
                time.sleep(0.2)
                # start onionshare http service in new thread
                self.mode.web_thread.start()
                self.success.emit()

        except (
            TorErrorInvalidSetting,
            TorErrorAutomatic,
            TorErrorSocketPort,
            TorErrorSocketFile,
            TorErrorMissingPassword,
            TorErrorUnreadableCookieFile,
            TorErrorAuthError,
            TorErrorProtocolError,
            BundledTorTimeout,
            BundledTorBroken,
            TorTooOldEphemeral,
            TorTooOldStealth,
            PortNotAvailable,
        ) as e:
            message = self.mode.common.gui.get_translated_tor_error(e)
            self.error.emit(message)
            return
        except Exception as e:
            # Handle any other error that wasn't in the list above
            message = strings._("error_generic").format(e.args[0])
            self.error.emit(message)
            return


class WebThread(QtCore.QThread):
    """
    Starts the web service
    """

    success = QtCore.Signal()
    error = QtCore.Signal(str)

    def __init__(self, mode):
        super(WebThread, self).__init__()
        self.mode = mode
        self.mode.common.log("WebThread", "__init__")

    def run(self):
        if not self.mode.is_server:
            return
        self.mode.common.log("WebThread", "run")
        try:
            self.mode.web.start(self.mode.app.port)
            self.success.emit()
        except WaitressException as e:
            message = self.mode.common.gui.get_translated_web_error(e)
            self.mode.common.log("WebThread", "run", message)
            self.error.emit(message)
            return


class AutoStartTimer(QtCore.QThread):
    """
    Waits for a prescribed time before allowing a share to start
    """

    success = QtCore.Signal()
    error = QtCore.Signal(str)

    def __init__(self, mode, canceled=False):
        super(AutoStartTimer, self).__init__()
        self.mode = mode
        self.canceled = canceled
        self.mode.common.log("AutoStartTimer", "__init__")

        # allow this thread to be terminated
        self.setTerminationEnabled()

    def run(self):
        now = QtCore.QDateTime.currentDateTime()
        autostart_timer_datetime_delta = now.secsTo(
            self.mode.server_status.autostart_timer_datetime
        )
        try:
            # Sleep until scheduled time
            while autostart_timer_datetime_delta > 0 and self.canceled is False:
                time.sleep(0.1)
                now = QtCore.QDateTime.currentDateTime()
                autostart_timer_datetime_delta = now.secsTo(
                    self.mode.server_status.autostart_timer_datetime
                )
            # Timer has now finished
            if self.canceled is False:
                self.mode.server_status.server_button.setText(
                    strings._("gui_please_wait")
                )
                self.mode.server_status_label.setText(
                    strings._("gui_status_indicator_share_working")
                )
                self.success.emit()
        except ValueError as e:
            self.error.emit(e.args[0])
            return


class EventHandlerThread(QtCore.QThread):
    """
    To trigger an event, write a JSON line to the events file. When that file changes,
    each line will be handled as an event. Valid events are:
    {"type": "new_tab"}
    {"type": "new_share_tab", "filenames": ["file1", "file2"]}
    """

    new_tab = QtCore.Signal()
    new_share_tab = QtCore.Signal(list)

    def __init__(self, common):
        super(EventHandlerThread, self).__init__()
        self.common = common
        self.common.log("EventHandlerThread", "__init__")
        self.should_quit = False

    def run(self):
        self.common.log("EventHandlerThread", "run")

        mtime = 0
        while True:
            if os.path.exists(self.common.gui.events_filename):
                # Events file exists
                if os.stat(self.common.gui.events_filename).st_mtime != mtime:
                    # Events file has been modified, load events
                    try:
                        with open(self.common.gui.events_filename, "r") as f:
                            lines = f.readlines()
                        os.remove(self.common.gui.events_filename)

                        self.common.log(
                            "EventHandler", "run", f"processing {len(lines)} lines"
                        )
                        for line in lines:
                            try:
                                obj = json.loads(line)
                                if "type" not in obj:
                                    self.common.log(
                                        "EventHandler",
                                        "run",
                                        f"event does not have a type: {obj}",
                                    )
                                    continue
                            except json.decoder.JSONDecodeError:
                                self.common.log(
                                    "EventHandler",
                                    "run",
                                    f"ignoring invalid line: {line}",
                                )
                                continue

                            if obj["type"] == "new_tab":
                                self.common.log("EventHandler", "run", "new_tab event")
                                self.new_tab.emit()

                            elif obj["type"] == "new_share_tab":
                                if (
                                    "filenames" in obj
                                    and type(obj["filenames"]) is list
                                ):
                                    self.new_share_tab.emit(obj["filenames"])
                                else:
                                    self.common.log(
                                        "EventHandler",
                                        "run",
                                        f"invalid new_share_tab event: {obj}",
                                    )

                            else:
                                self.common.log(
                                    "EventHandler", "run", f"invalid event type: {obj}"
                                )

                    except Exception:
                        pass

            if self.should_quit:
                break
            time.sleep(0.2)


class OnionCleanupThread(QtCore.QThread):
    """
    Wait for Tor rendezvous circuits to close in a separate thread
    """

    def __init__(self, common):
        super(OnionCleanupThread, self).__init__()
        self.common = common
        self.common.log("OnionCleanupThread", "__init__")

    def run(self):
        self.common.log("OnionCleanupThread", "run")
        self.common.gui.onion.cleanup()


class DownloadThread(QtCore.QThread):
    """
    Download an Onion share in a separate thread (for Download Mode)
    """

    begun = QtCore.Signal()
    progress = QtCore.Signal(int)  # progress percentage
    success = QtCore.Signal(
        str, str, int
    )  # Emit file_path (str), file_name (str), and file_size (int)
    error = QtCore.Signal(str)
    locked = QtCore.Signal()

    def __init__(self, mode):
        super(DownloadThread, self).__init__()
        self._mutex = QtCore.QMutex()  # Mutex for locking
        self._lock = False  # To track the lock status

        self.mode = mode
        self.mode.common.log("DownloadThread", "__init__")

        self.saved_download_mode_dir = None

    def run(self):
        if self._mutex.tryLock():
            self._lock = True
            self.mode.common.log("DownloadThread", "run", "Lock claimed")
            self.begun.emit()

            try:
                self.mode.common.log("DownloadThread", "run")
                if self.mode.common.gui.local_only:
                    proxies = {}
                else:
                    # Obtain the SocksPort from Tor and set it as the proxies for Requests
                    (socks_address, socks_port) = (
                        self.mode.common.gui.onion.get_tor_socks_port()
                    )
                    proxies = {
                        "http": f"socks5h://{socks_address}:{socks_port}",
                        "https": f"socks5h://{socks_address}:{socks_port}",
                    }

                # We only support the /download (zip) route for Share Mode right now
                # (no individual file downloads)
                url = f"http://{self.mode.service_id}.onion/download"

                # Set up Client Auth if required
                if (
                    self.mode.onionshare_uses_private_key_checkbox.isChecked()
                    and len(self.mode.onionshare_private_key.text().strip()) == 52
                ):
                    self.mode.common.log(
                        "DownloadThread", "run", f"Setting private key"
                    )
                    self.mode.common.gui.onion.add_onion_client_auth(
                        self.mode.service_id,
                        self.mode.onionshare_private_key.text().strip(),
                    )

                response = requests.get(url, proxies=proxies, stream=True)

                # Check if the request was successful (HTTP status code 200)
                if response.status_code == 200:
                    # Extract the file name from the 'Content-Disposition' header, if present
                    file_name = self.get_filename_from_content_disposition(
                        response.headers
                    )
                    self.mode.common.log(
                        "DownloadThread",
                        "run",
                        f"file_name is {file_name}, now we will try and write it",
                    )

                    # Get the file size from the 'Content-Length' header
                    file_size = int(response.headers.get("Content-Length", 0))

                    # Save the share
                    file_path = self.save_share(file_name, response, file_size)
                    self.mode.common.log(
                        "DownloadThread",
                        "run",
                        f"file_path is {file_path}, we saved it",
                    )

                    # Emit the file path, file name, and file size to DownloadMode's add_download_item()
                    self.success.emit(file_path, file_name, file_size)
                else:
                    raise Exception(
                        f"Failed to download file. Status code: {response.status_code}"
                    )

            except Exception as e:
                self.mode.common.log(
                    "DownloadThread", "run", f"Error occurred in requests: {e}"
                )
                self.error.emit(str(e))
                return

            finally:
                # Always release the mutex, even if an exception occurred
                self._mutex.unlock()
                self._lock = False
        else:
            self.mode.common.log(
                "DownloadThread",
                "run",
                "Lock was in place, maybe the last download was still occurring?",
            )
            self.locked.emit()

    def get_filename_from_content_disposition(self, headers):
        content_disposition = headers.get("Content-Disposition", "")

        # Extract filename directly from Content-Disposition
        if "filename" in content_disposition:
            # Extract the filename (it could contain the UTF-8 encoded form as well)
            filename = (
                content_disposition.split("filename=")[1].split(";")[0].strip('"')
            )
        elif "filename*" in content_disposition:
            # Extract and decode filename* if filename* is used
            filename = unquote(
                content_disposition.split("filename*=UTF-8''")[1].strip('"')
            )
        else:
            # Fallback default filename
            filename = "downloaded_file.zip"

        return filename

    def save_share(self, file_name, response, file_size):
        """
        Write the downloaded share to disk. This is similar to ReceiveMode,
        in that we try to create a unique timestamp-based directory to save
        to.

        The exception is if we are in polling mode, in which case, we want
        to continually overwrite the existing download with a new version,
        to keep it up to date.
        """
        if self.mode.is_polling and self.mode.history.completed_count > 0:
            download_mode_dir = self.saved_download_mode_dir

        else:
            now = datetime.now()
            date_dir = now.strftime("%Y-%m-%d")
            time_dir = now.strftime("%H%M%S%f")
            download_mode_dir = os.path.join(
                self.mode.settings.get("download", "data_dir"), date_dir, time_dir
            )

            # Create that directory, which shouldn't exist yet
            try:
                os.makedirs(download_mode_dir, 0o700, exist_ok=False)
            except OSError:
                # If this directory already exists, maybe someone else is downloading files at
                # the same second in another tab, so use a different name in that case
                if os.path.exists(download_mode_dir):
                    # Keep going until we find a directory name that's available
                    i = 1
                    while True:
                        new_download_mode_dir = f"{download_mode_dir}-{i}"
                        try:
                            os.makedirs(new_download_mode_dir, 0o700, exist_ok=False)
                            download_mode_dir = new_download_mode_dir
                            break
                        except OSError:
                            pass
                        i += 1
                        # Failsafe
                        if i == 100:
                            self.mode.common.log(
                                "DownloadThread",
                                "save_share",
                                "Error finding available download directory",
                            )
                            raise Exception(
                                "Error finding available download directory"
                            )
            except PermissionError:
                raise Exception("Permission denied creating download directory")

        # Save this successful download dir if we are in polling mode, so we can
        # use it next time.
        if self.mode.is_polling and self.mode.history.completed_count == 0:
            self.saved_download_mode_dir = download_mode_dir

        # Build file path for saving
        file_path = os.path.join(download_mode_dir, file_name)
        self.mode.common.log(
            "DownloadThread",
            "save_share",
            f"File path: {file_path}",
        )

        # Save the file and report the progress back to the UI
        with open(file_path, "wb") as file:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024):  # 1KB chunks
                if chunk:
                    downloaded += len(chunk)  # Update the downloaded bytes

                    # Send progress via signal to the main thread
                    progress = int((downloaded / file_size) * 100)
                    self.progress.emit(progress)

                    file.write(chunk)
        return file_path
