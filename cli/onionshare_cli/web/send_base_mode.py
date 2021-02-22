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

import os
import sys
import tempfile
import mimetypes
import gzip
from flask import Response, request, render_template, make_response
from unidecode import unidecode
from werkzeug.urls import url_quote


class SendBaseModeWeb:
    """
    All of the web logic shared between share and website mode (modes where the user sends files)
    """

    def __init__(self, common, web):
        super(SendBaseModeWeb, self).__init__()
        self.common = common
        self.web = web

        # Information about the file to be shared
        self.is_zipped = False
        self.download_filename = None
        self.download_filesize = None
        self.gzip_filename = None
        self.gzip_filesize = None
        self.zip_writer = None

        # If autostop_sharing, only allow one download at a time
        self.download_in_progress = False

        # This tracks the history id
        self.cur_history_id = 0

        self.define_routes()
        self.init()

    def set_file_info(self, filenames, processed_size_callback=None):
        """
        Build a data structure that describes the list of files
        """
        # If there's just one folder, replace filenames with a list of files inside that folder
        if len(filenames) == 1 and os.path.isdir(filenames[0]):
            filenames = [
                os.path.join(filenames[0], x) for x in os.listdir(filenames[0])
            ]

        # Re-initialize
        self.files = {}  # Dictionary mapping file paths to filenames on disk
        self.root_files = (
            {}
        )  # This is only the root files and dirs, as opposed to all of them
        self.cleanup_filenames = []
        self.cur_history_id = 0
        self.file_info = {"files": [], "dirs": []}
        self.gzip_individual_files = {}
        self.init()

        # Build the file list
        for filename in filenames:
            basename = os.path.basename(filename.rstrip("/"))

            # If it's a filename, add it
            if os.path.isfile(filename):
                self.files[basename] = filename
                self.root_files[basename] = filename

            # If it's a directory, add it recursively
            elif os.path.isdir(filename):
                self.root_files[basename] = filename

                for root, _, nested_filenames in os.walk(filename):
                    # Normalize the root path. So if the directory name is "/home/user/Documents/some_folder",
                    # and it has a nested folder foobar, the root is "/home/user/Documents/some_folder/foobar".
                    # The normalized_root should be "some_folder/foobar"
                    normalized_root = os.path.join(
                        basename, root[len(filename) :].lstrip("/")
                    ).rstrip("/")

                    # Add the dir itself
                    self.files[normalized_root] = root

                    # Add the files in this dir
                    for nested_filename in nested_filenames:
                        self.files[
                            os.path.join(normalized_root, nested_filename)
                        ] = os.path.join(root, nested_filename)

        self.set_file_info_custom(filenames, processed_size_callback)

    def directory_listing(self, filenames, path="", filesystem_path=None):
        # Tell the GUI about the directory listing
        history_id = self.cur_history_id
        self.cur_history_id += 1
        self.web.add_request(
            self.web.REQUEST_INDIVIDUAL_FILE_STARTED,
            f"/{path}",
            {"id": history_id, "method": request.method, "status_code": 200},
        )

        breadcrumbs = [("☗", "/")]
        parts = path.split("/")
        if parts[-1] == "":
            parts = parts[:-1]
        for i in range(len(parts)):
            breadcrumbs.append((parts[i], f"/{'/'.join(parts[0 : i + 1])}"))
        breadcrumbs_leaf = breadcrumbs.pop()[0]

        # If filesystem_path is None, this is the root directory listing
        files, dirs = self.build_directory_listing(path, filenames, filesystem_path)
        r = self.directory_listing_template(
            path, files, dirs, breadcrumbs, breadcrumbs_leaf
        )
        return self.web.add_security_headers(r)

    def build_directory_listing(self, path, filenames, filesystem_path):
        files = []
        dirs = []

        for filename in filenames:
            if filesystem_path:
                this_filesystem_path = os.path.join(filesystem_path, filename)
            else:
                this_filesystem_path = self.files[filename]

            is_dir = os.path.isdir(this_filesystem_path)

            if is_dir:
                dirs.append(
                    {"link": os.path.join(f"/{path}", filename), "basename": filename}
                )
            else:
                size = os.path.getsize(this_filesystem_path)
                size_human = self.common.human_readable_filesize(size)
                files.append(
                    {
                        "link": os.path.join(f"/{path}", filename),
                        "basename": filename,
                        "size_human": size_human,
                    }
                )

        return files, dirs

    def stream_individual_file(self, filesystem_path):
        """
        Return a flask response that's streaming the download of an individual file, and gzip
        compressing it if the browser supports it.
        """
        use_gzip = self.should_use_gzip()

        # gzip compress the individual file, if it hasn't already been compressed
        if use_gzip:
            if filesystem_path not in self.gzip_individual_files:
                gzip_filename = tempfile.mkstemp("wb+")[1]
                self._gzip_compress(filesystem_path, gzip_filename, 6, None)
                self.gzip_individual_files[filesystem_path] = gzip_filename

                # Make sure the gzip file gets cleaned up when onionshare stops
                self.cleanup_filenames.append(gzip_filename)

            file_to_download = self.gzip_individual_files[filesystem_path]
            filesize = os.path.getsize(self.gzip_individual_files[filesystem_path])
        else:
            file_to_download = filesystem_path
            filesize = os.path.getsize(filesystem_path)

        path = request.path

        # Tell GUI the individual file started
        history_id = self.cur_history_id
        self.cur_history_id += 1

        # Only GET requests are allowed, any other method should fail
        if request.method != "GET":
            return self.web.error405(history_id)

        self.web.add_request(
            self.web.REQUEST_INDIVIDUAL_FILE_STARTED,
            path,
            {"id": history_id, "filesize": filesize},
        )

        def generate():
            chunk_size = 102400  # 100kb

            fp = open(file_to_download, "rb")
            done = False
            while not done:
                chunk = fp.read(chunk_size)
                if chunk == b"":
                    done = True
                else:
                    try:
                        yield chunk

                        # Tell GUI the progress
                        downloaded_bytes = fp.tell()
                        percent = (1.0 * downloaded_bytes / filesize) * 100
                        if (
                            not self.web.is_gui
                            or self.common.platform == "Linux"
                            or self.common.platform == "BSD"
                        ):
                            sys.stdout.write(
                                "\r{0:s}, {1:.2f}%          ".format(
                                    self.common.human_readable_filesize(
                                        downloaded_bytes
                                    ),
                                    percent,
                                )
                            )
                            sys.stdout.flush()

                        self.web.add_request(
                            self.web.REQUEST_INDIVIDUAL_FILE_PROGRESS,
                            path,
                            {
                                "id": history_id,
                                "bytes": downloaded_bytes,
                                "filesize": filesize,
                            },
                        )
                        done = False
                    except:
                        # Looks like the download was canceled
                        done = True

                        # Tell the GUI the individual file was canceled
                        self.web.add_request(
                            self.web.REQUEST_INDIVIDUAL_FILE_CANCELED,
                            path,
                            {"id": history_id},
                        )

            fp.close()

            if self.common.platform != "Darwin":
                sys.stdout.write("\n")

        basename = os.path.basename(filesystem_path)

        r = Response(generate())
        if use_gzip:
            r.headers.set("Content-Encoding", "gzip")
        r.headers.set("Content-Length", filesize)
        filename_dict = {
            "filename": unidecode(basename),
            "filename*": "UTF-8''%s" % url_quote(basename),
        }
        r.headers.set("Content-Disposition", "inline", **filename_dict)
        r = self.web.add_security_headers(r)
        (content_type, _) = mimetypes.guess_type(basename, strict=False)
        if content_type is not None:
            r.headers.set("Content-Type", content_type)
        return r

    def should_use_gzip(self):
        """
        Should we use gzip for this browser?
        """
        return (not self.is_zipped) and (
            "gzip" in request.headers.get("Accept-Encoding", "").lower()
        )

    def _gzip_compress(
        self, input_filename, output_filename, level, processed_size_callback=None
    ):
        """
        Compress a file with gzip, without loading the whole thing into memory
        Thanks: https://stackoverflow.com/questions/27035296/python-how-to-gzip-a-large-text-file-without-memoryerror
        """
        bytes_processed = 0
        blocksize = 1 << 16  # 64kB
        with open(input_filename, "rb") as input_file:
            output_file = gzip.open(output_filename, "wb", level)
            while True:
                if processed_size_callback is not None:
                    processed_size_callback(bytes_processed)

                block = input_file.read(blocksize)
                if len(block) == 0:
                    break
                output_file.write(block)
                bytes_processed += blocksize

            output_file.close()

    def init(self):
        """
        Inherited class will implement this
        """
        pass

    def define_routes(self):
        """
        Inherited class will implement this
        """
        pass

    def directory_listing_template(self):
        """
        Inherited class will implement this. It should call render_template and return
        the response.
        """
        pass

    def set_file_info_custom(self, filenames, processed_size_callback):
        """
        Inherited class will implement this.
        """
        pass

    def render_logic(self, path=""):
        """
        Inherited class will implement this.
        """
        pass
