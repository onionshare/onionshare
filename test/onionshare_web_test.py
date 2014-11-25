"""
OnionShare | https://onionshare.org/

Copyright (C) 2014 Micah Lee <micah@micahflee.com>

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
from onionshare import web
from nose import with_setup


def test_generate_slug_length():
    """generates a 26-character slug"""
    assert len(web.slug) == 26


def test_generate_slug_characters():
    """generates a base32-encoded slug"""

    def is_b32(string):
        b32_alphabet = "01234556789abcdefghijklmnopqrstuvwxyz"
        return all(char in b32_alphabet for char in string)

    assert is_b32(web.slug)
