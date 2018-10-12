import pytest
import subprocess

from tempfile import NamedTemporaryFile
from werkzeug.exceptions import RequestedRangeNotSatisfiable

from onionshare.web.share_mode import parse_range_header


VALID_RANGES = [
    (None, 500, [(0, 499)]),
    ('bytes=0', 500, [(0, 499)]),
    ('bytes=100', 500, [(100, 499)]),
    ('bytes=100-', 500, [(100, 499)]),  # not in the RFC, but how curl sends
    ('bytes=0-99', 500, [(0, 99)]),
    ('bytes=0-599', 500, [(0, 499)]),
    ('bytes=0-0', 500, [(0, 0)]),
    ('bytes=-100', 500, [(400, 499)]),
    ('bytes=0-99,100-199', 500, [(0, 199)]),
    ('bytes=0-100,100-199', 500, [(0, 199)]),
    ('bytes=0-99,101-199', 500, [(0, 99), (101, 199)]),
    ('bytes=0-199,100-299', 500, [(0, 299)]),
    ('bytes=0-99,200-299', 500, [(0, 99), (200, 299)]),
]


INVALID_RANGES = [
    'bytes=200-100',
    'bytes=0-100,300-200',
]


def test_parse_ranges():
    for case in VALID_RANGES:
        (header, target_size, expected) = case
        parsed = parse_range_header(header, target_size)
        assert parsed == expected, case

    for invalid in INVALID_RANGES:
        with pytest.raises(RequestedRangeNotSatisfiable):
            parse_range_header(invalid, 500)
