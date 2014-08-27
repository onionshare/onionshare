from onionshare import web
from nose import with_setup

def test_generate_slug_length():
    "generates a 26-character slug"
    assert len(web.slug) == 26

def test_generate_slug_characters():
    "generates a base32-encoded slug"

    def is_b32(string):
        b32_alphabet = "01234556789abcdefghijklmnopqrstuvwxyz"
        return all(char in b32_alphabet for char in string)

    assert is_b32(web.slug)


