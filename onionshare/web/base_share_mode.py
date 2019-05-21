import os
import sys
import tempfile
import zipfile
import mimetypes
import gzip
from flask import Response, request, render_template, make_response

from .. import strings


class ShareModeWeb(object):
    """
    This is the base class that includes shared functionality between share mode
    and website mode
    """
    def __init__(self, common, web):
        self.common = common
        self.web = web
