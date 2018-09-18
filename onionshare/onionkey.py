# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2017 Micah Lee <micah@micahflee.com>

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

import base64
import hashlib
# Need sha3 if python version is older than 3.6, otherwise
# we can't use hashlib.sha3_256
if sys.version_info < (3, 6):
    import sha3

import nacl.signing

from Crypto.PublicKey import RSA

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def stem_compatible_base64_blob_from_private_key(private_key_seed: bytes) -> str:
    """
    Provides a base64-encoded private key for v3-style Onions.
    """
    b = 256

    def bit(h: bytes, i: int) -> int:
        return (h[i // 8] >> (i % 8)) & 1

    def encode_int(y: int) -> bytes:
        bits = [(y >> i) & 1 for i in range(b)]
        return b''.join([bytes([(sum([bits[i * 8 + j] << j for j in range(8)]))]) for i in range(b // 8)])

    def expand_private_key(sk: bytes) -> bytes:
        h = hashlib.sha512(sk).digest()
        a = 2 ** (b - 2) + sum(2 ** i * bit(h, i) for i in range(3, b - 2))
        k = b''.join([bytes([h[i]]) for i in range(b // 8, b // 4)])
        assert len(k) == 32
        return encode_int(a) + k

    expanded_private_key = expand_private_key(private_key_seed)
    return base64.b64encode(expanded_private_key).decode()


def onion_url_from_private_key(private_key_seed: bytes) -> str:
    """
    Derives the public key (.onion hostname) from a v3-style
    Onion private key.
    """
    signing_key = nacl.signing.SigningKey(seed=private_key_seed)
    public_key = bytes(signing_key.verify_key)
    version = b'\x03'
    checksum = hashlib.sha3_256(b".onion checksum" + public_key + version).digest()[:2]
    onion_address = "http://{}.onion".format(base64.b32encode(public_key + checksum + version).decode().lower())
    return onion_address


def generate_v3_private_key():
    """
    Generates a private and public key for use with v3 style Onions.
    Returns both the private key as well as the public key (.onion hostname)
    """
    private_key_seed = os.urandom(32)
    private_key = stem_compatible_base64_blob_from_private_key(private_key_seed)
    onion_url = onion_url_from_private_key(private_key_seed)
    return (private_key, onion_url)


def generate_v2_private_key():
    """
    Generates a private and public key for use with v2 style Onions.
    Returns both the serialized private key (compatible with Stem)
    as well as the public key (.onion hostname)
    """
    # Generate v2 Onion Service private key
    private_key = rsa.generate_private_key(public_exponent=65537,
                                           key_size=1024,
                                           backend=default_backend())
    hs_public_key = private_key.public_key()

    # Pre-generate the public key (.onion hostname)
    der_format = hs_public_key.public_bytes(encoding=serialization.Encoding.DER,
                                            format=serialization.PublicFormat.PKCS1)

    onion_url = base64.b32encode(hashlib.sha1(der_format).digest()[:-10]).lower().decode()

    # Generate Stem-compatible key content
    pem_format = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                           format=serialization.PrivateFormat.TraditionalOpenSSL,
                                           encryption_algorithm=serialization.NoEncryption())
    serialized_key = ''.join(pem_format.decode().split('\n')[1:-2])

    return (serialized_key, onion_url)


def is_v2_key(key):
    """
    Helper function for determining if a key is RSA1024 (v2) or not.
    """
    try:
        # Import the key
        key = RSA.importKey(base64.b64decode(key))
        # Is this a v2 Onion key? (1024 bits) If so, we should keep using it.
        if key.n.bit_length() == 1024:
            return True
        else:
            return False
    except:
        return False

