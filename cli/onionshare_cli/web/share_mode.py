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

import binascii
import hashlib
import os
import sys
import tempfile
import zipfile
import mimetypes
from datetime import datetime
from flask import Response, request, render_template, make_response, abort
from unidecode import unidecode
from werkzeug.http import parse_date, http_date
from werkzeug.urls import url_quote

from .send_base_mode import SendBaseModeWeb


def make_etag(data):
    hasher = hashlib.sha256()

    while True:
        read_bytes = data.read(4096)
        if read_bytes:
            hasher.update(read_bytes)
        else:
            break

    hash_value = binascii.hexlify(hasher.digest()).decode("utf-8")
    return '"sha256:{}"'.format(hash_value)


def parse_range_header(range_header: str, target_size: int) -> list:
    end_index = target_size - 1
    if range_header is None:
        return [(0, end_index)]

    bytes_ = "bytes="
    if not range_header.startswith(bytes_):
        abort(416)

    ranges = []
    for range_ in range_header[len(bytes_) :].split(","):
        split = range_.split("-")
        if len(split) == 1:
            try:
                start = int(split[0])
                end = end_index
            except ValueError:
                abort(416)
        elif len(split) == 2:
            start, end = split[0], split[1]
            if not start:
                # parse ranges of the form "bytes=-100" (i.e., last 100 bytes)
                end = end_index
                try:
                    start = end - int(split[1]) + 1
                except ValueError:
                    abort(416)
            else:
                # parse ranges of the form "bytes=100-200"
                try:
                    start = int(start)
                    if not end:
                        end = target_size
                    else:
                        end = int(end)
                except ValueError:
                    abort(416)

                if end < start:
                    abort(416)

                end = min(end, end_index)
        else:
            abort(416)

        ranges.append((start, end))

    # merge the ranges
    merged = []
    ranges = sorted(ranges, key=lambda x: x[0])
    for range_ in ranges:
        # initial case
        if not merged:
            merged.append(range_)
        else:
            # merge ranges that are adjacent or overlapping
            if range_[0] <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(range_[1], merged[-1][1]))
            else:
                merged.append(range_)

    return merged


class ShareModeWeb(SendBaseModeWeb):
    """
    All of the web logic for share mode
    """

    def init(self):
        self.common.log("ShareModeWeb", "init")

        # Allow downloading individual files if "Stop sharing after files have been sent" is unchecked
        self.download_individual_files = not self.web.settings.get(
            "share", "autostop_sharing"
        )

        self.download_etag = None
        self.gzip_etag = None
        self.last_modified = datetime.utcnow()

    def define_routes(self):
        """
        The web app routes for sharing files
        """

        @self.web.app.route("/", defaults={"path": ""}, methods=["GET"], provide_automatic_options=False)
        @self.web.app.route("/<path:path>", methods=["GET"], provide_automatic_options=False)
        def index(path):
            """
            Render the template for the onionshare landing page.
            """
            self.web.add_request(self.web.REQUEST_LOAD, request.path)

            # Deny new downloads if "Stop sharing after files have been sent" is checked and there is
            # currently a download
            deny_download = (
                self.web.settings.get("share", "autostop_sharing")
                and self.download_in_progress
            )
            if deny_download:
                r = make_response(render_template("denied.html"))
                return self.web.add_security_headers(r)

            # If download is allowed to continue, serve download page
            if self.should_use_gzip():
                self.filesize = self.gzip_filesize
            else:
                self.filesize = self.download_filesize

            return self.render_logic(path)

        @self.web.app.route("/download", methods=["GET"], provide_automatic_options=False)
        def download():
            """
            Download the zip file.
            """
            # Deny new downloads if "Stop After First Download" is checked and there is
            # currently a download
            deny_download = (
                self.web.settings.get("share", "autostop_sharing")
                and self.download_in_progress
            )
            if deny_download:
                r = make_response(render_template("denied.html"))
                return self.web.add_security_headers(r)

            # Prepare some variables to use inside generate() function below
            # which is outside of the request context
            shutdown_func = request.environ.get("werkzeug.server.shutdown")
            request_path = request.path

            # If this is a zipped file, then serve as-is. If it's not zipped, then,
            # if the http client supports gzip compression, gzip the file first
            # and serve that
            use_gzip = self.should_use_gzip()
            if use_gzip:
                file_to_download = self.gzip_filename
                self.filesize = self.gzip_filesize
                etag = self.gzip_etag
            else:
                file_to_download = self.download_filename
                self.filesize = self.download_filesize
                etag = self.download_etag

            # for range requests
            range_, status_code = self.get_range_and_status_code(
                self.filesize, etag, self.last_modified
            )

            # Tell GUI the download started
            history_id = self.cur_history_id
            self.cur_history_id += 1
            self.web.add_request(
                self.web.REQUEST_STARTED,
                request_path,
                {"id": history_id, "use_gzip": use_gzip},
            )

            basename = os.path.basename(self.download_filename)

            if status_code == 304:
                r = Response()
            else:
                r = Response(
                    self.generate(
                        shutdown_func,
                        range_,
                        file_to_download,
                        request_path,
                        history_id,
                        self.filesize,
                    )
                )

            if use_gzip:
                r.headers.set("Content-Encoding", "gzip")

            r.headers.set("Content-Length", range_[1] - range_[0] + 1)
            filename_dict = {
                "filename": unidecode(basename),
                "filename*": "UTF-8''%s" % url_quote(basename),
            }
            r.headers.set("Content-Disposition", "attachment", **filename_dict)
            r = self.web.add_security_headers(r)
            # guess content type
            (content_type, _) = mimetypes.guess_type(basename, strict=False)
            if content_type is not None:
                r.headers.set("Content-Type", content_type)
            r.headers.set("Accept-Ranges", "bytes")
            r.headers.set("ETag", etag)
            r.headers.set("Last-Modified", http_date(self.last_modified))
            # we need to set this for range requests
            r.headers.set("Vary", "Accept-Encoding")

            if status_code == 206:
                r.headers.set(
                    "Content-Range",
                    "bytes {}-{}/{}".format(range_[0], range_[1], self.filesize),
                )

            r.status_code = status_code

            return r

    @classmethod
    def get_range_and_status_code(cls, dl_size, etag, last_modified):
        use_default_range = True
        status_code = 200
        range_header = request.headers.get("Range")

        # range requests are only allowed for get
        if request.method == "GET":
            ranges = parse_range_header(range_header, dl_size)
            if not (
                len(ranges) == 1 and ranges[0][0] == 0 and ranges[0][1] == dl_size - 1
            ):
                use_default_range = False
                status_code = 206

            if range_header:
                if_range = request.headers.get("If-Range")
                if if_range and if_range != etag:
                    use_default_range = True
                    status_code = 200

        if use_default_range:
            ranges = [(0, dl_size - 1)]

        if len(ranges) > 1:
            abort(416)  # We don't support multipart range requests yet
        range_ = ranges[0]

        etag_header = request.headers.get("ETag")
        if etag_header is not None and etag_header != etag:
            abort(412)

        if_unmod = request.headers.get("If-Unmodified-Since")
        if if_unmod:
            if_date = parse_date(if_unmod)
            if if_date and if_date > last_modified:
                abort(412)
            elif range_header is None:
                status_code = 304

        return range_, status_code

    def generate(
        self, shutdown_func, range_, file_to_download, path, history_id, filesize
    ):
        # The user hasn't canceled the download
        self.client_cancel = False

        # Starting a new download
        if self.web.settings.get("share", "autostop_sharing"):
            self.download_in_progress = True

        start, end = range_

        chunk_size = 102400  # 100kb

        fp = open(file_to_download, "rb")
        fp.seek(start)
        self.web.done = False
        canceled = False
        bytes_left = end - start + 1
        while not self.web.done:
            # The user has canceled the download, so stop serving the file
            if not self.web.stop_q.empty():
                self.web.add_request(
                    self.web.REQUEST_CANCELED, path, {"id": history_id}
                )
                break

            read_size = min(chunk_size, bytes_left)
            chunk = fp.read(read_size)
            if chunk == b"":
                self.web.done = True
            else:
                try:
                    yield chunk

                    # tell GUI the progress
                    downloaded_bytes = fp.tell()
                    percent = (1.0 * downloaded_bytes / filesize) * 100
                    bytes_left -= read_size

                    # only output to stdout if running onionshare in CLI mode, or if using Linux (#203, #304)
                    if (
                        not self.web.is_gui
                        or self.common.platform == "Linux"
                        or self.common.platform == "BSD"
                    ):
                        sys.stdout.write(
                            "\r{0:s}, {1:.2f}%          ".format(
                                self.common.human_readable_filesize(downloaded_bytes),
                                percent,
                            )
                        )
                        sys.stdout.flush()

                    self.web.add_request(
                        self.web.REQUEST_PROGRESS,
                        path,
                        {
                            "id": history_id,
                            "bytes": downloaded_bytes,
                            "total_bytes": filesize,
                        },
                    )
                    self.web.done = False
                except Exception:
                    # looks like the download was canceled
                    self.web.done = True
                    canceled = True

                    # tell the GUI the download has canceled
                    self.web.add_request(
                        self.web.REQUEST_CANCELED, path, {"id": history_id}
                    )

        fp.close()

        if self.common.platform != "Darwin":
            sys.stdout.write("\n")

        # Download is finished
        if self.web.settings.get("share", "autostop_sharing"):
            self.download_in_progress = False

        # Close the server, if necessary
        if self.web.settings.get("share", "autostop_sharing") and not canceled:
            print("Stopped because transfer is complete")
            self.web.running = False
            try:
                if shutdown_func is None:
                    raise RuntimeError("Not running with the Werkzeug Server")
                shutdown_func()
            except Exception:
                pass

    def directory_listing_template(
        self, path, files, dirs, breadcrumbs, breadcrumbs_leaf
    ):
        return make_response(
            render_template(
                "send.html",
                file_info=self.file_info,
                files=files,
                dirs=dirs,
                breadcrumbs=breadcrumbs,
                breadcrumbs_leaf=breadcrumbs_leaf,
                filename=os.path.basename(self.download_filename),
                filesize=self.filesize,
                filesize_human=self.common.human_readable_filesize(
                    self.download_filesize
                ),
                is_zipped=self.is_zipped,
                static_url_path=self.web.static_url_path,
                download_individual_files=self.download_individual_files,
                title=self.web.settings.get("general", "title"),
            )
        )

    def set_file_info_custom(self, filenames, processed_size_callback):
        self.common.log("ShareModeWeb", "set_file_info_custom")
        self.web.cancel_compression = False
        self.build_zipfile_list(filenames, processed_size_callback)

    def render_logic(self, path=""):
        if path in self.files:
            filesystem_path = self.files[path]

            # If it's a directory
            if os.path.isdir(filesystem_path):
                # Render directory listing
                filenames = []
                for filename in os.listdir(filesystem_path):
                    if os.path.isdir(os.path.join(filesystem_path, filename)):
                        filenames.append(filename + "/")
                    else:
                        filenames.append(filename)
                filenames.sort()
                return self.directory_listing(filenames, path, filesystem_path)

            # If it's a file
            elif os.path.isfile(filesystem_path):
                if self.download_individual_files:
                    return self.stream_individual_file(filesystem_path)
                else:
                    history_id = self.cur_history_id
                    self.cur_history_id += 1
                    return self.web.error404(history_id)

            # If it's not a directory or file, throw a 404
            else:
                history_id = self.cur_history_id
                self.cur_history_id += 1
                return self.web.error404(history_id)
        else:
            # Special case loading /

            if path == "":
                # Root directory listing
                filenames = list(self.root_files)
                filenames.sort()
                return self.directory_listing(filenames, path)

            else:
                # If the path isn't found, throw a 404
                history_id = self.cur_history_id
                self.cur_history_id += 1
                return self.web.error404(history_id)

    def build_zipfile_list(self, filenames, processed_size_callback=None):
        self.common.log("ShareModeWeb", "build_zipfile_list")
        for filename in filenames:
            info = {
                "filename": filename,
                "basename": os.path.basename(filename.rstrip("/")),
            }
            if os.path.isfile(filename):
                info["size"] = os.path.getsize(filename)
                info["size_human"] = self.common.human_readable_filesize(info["size"])
                self.file_info["files"].append(info)
            if os.path.isdir(filename):
                info["size"] = self.common.dir_size(filename)
                info["size_human"] = self.common.human_readable_filesize(info["size"])
                self.file_info["dirs"].append(info)
        self.file_info["files"].sort(key=lambda k: k["basename"])
        self.file_info["dirs"].sort(key=lambda k: k["basename"])

        # Check if there's only 1 file and no folders
        if len(self.file_info["files"]) == 1 and len(self.file_info["dirs"]) == 0:
            self.download_filename = self.file_info["files"][0]["filename"]
            self.download_filesize = self.file_info["files"][0]["size"]
            with open(self.download_filename, "rb") as f:
                self.download_etag = make_etag(f)

            # Compress the file with gzip now, so we don't have to do it on each request
            self.gzip_filename = tempfile.mkstemp("wb+")[1]
            self._gzip_compress(
                self.download_filename, self.gzip_filename, 6, processed_size_callback
            )
            self.gzip_filesize = os.path.getsize(self.gzip_filename)
            with open(self.gzip_filename, "rb") as f:
                self.gzip_etag = make_etag(f)

            # Make sure the gzip file gets cleaned up when onionshare stops
            self.web.cleanup_filenames.append(self.gzip_filename)

            self.is_zipped = False

        else:
            # Zip up the files and folders
            self.zip_writer = ZipWriter(
                self.common, processed_size_callback=processed_size_callback
            )
            self.download_filename = self.zip_writer.zip_filename
            for info in self.file_info["files"]:
                self.zip_writer.add_file(info["filename"])
                # Canceling early?
                if self.web.cancel_compression:
                    self.zip_writer.close()
                    return False

            for info in self.file_info["dirs"]:
                if not self.zip_writer.add_dir(info["filename"]):
                    return False

            self.zip_writer.close()
            self.download_filesize = os.path.getsize(self.download_filename)
            with open(self.download_filename, "rb") as f:
                self.download_etag = make_etag(f)

            # Make sure the zip file gets cleaned up when onionshare stops
            self.web.cleanup_filenames.append(self.zip_writer.zip_filename)
            self.web.cleanup_filenames.append(self.zip_writer.zip_temp_dir)

            self.is_zipped = True

        return True


class ZipWriter(object):
    """
    ZipWriter accepts files and directories and compresses them into a zip file
    with. If a zip_filename is not passed in, it will use the default onionshare
    filename.
    """

    def __init__(self, common, zip_filename=None, processed_size_callback=None):
        self.common = common
        self.cancel_compression = False

        if zip_filename:
            self.zip_filename = zip_filename
        else:
            self.zip_temp_dir = tempfile.mkdtemp()
            self.zip_filename = (
                f"{self.zip_temp_dir}/onionshare_{self.common.random_string(4, 6)}.zip"
            )

        self.z = zipfile.ZipFile(self.zip_filename, "w", allowZip64=True)
        self.processed_size_callback = processed_size_callback
        if self.processed_size_callback is None:
            self.processed_size_callback = lambda _: None
        self._size = 0
        self.processed_size_callback(self._size)

    def add_file(self, filename):
        """
        Add a file to the zip archive.
        """
        self.z.write(filename, os.path.basename(filename), zipfile.ZIP_DEFLATED)
        self._size += os.path.getsize(filename)
        self.processed_size_callback(self._size)

    def add_dir(self, filename):
        """
        Add a directory, and all of its children, to the zip archive.
        """
        dir_to_strip = os.path.dirname(filename.rstrip("/")) + "/"
        for dirpath, dirnames, filenames in os.walk(filename):
            for f in filenames:
                # Canceling early?
                if self.cancel_compression:
                    return False

                full_filename = os.path.join(dirpath, f)
                if not os.path.islink(full_filename):
                    arc_filename = full_filename[len(dir_to_strip) :]
                    self.z.write(full_filename, arc_filename, zipfile.ZIP_DEFLATED)
                    self._size += os.path.getsize(full_filename)
                    self.processed_size_callback(self._size)

        return True

    def close(self):
        """
        Close the zip archive.
        """
        self.z.close()
