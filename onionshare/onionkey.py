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

import base64
import hashlib
import os

import nacl.signing

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


b = 256

def bit(h, i):
    return (h[i // 8] >> (i % 8)) & 1


def encodeint(y):
    bits = [(y >> i) & 1 for i in range(b)]
    return b''.join([bytes([(sum([bits[i * 8 + j] << j for j in range(8)]))]) for i in range(b // 8)])


def H(m):
    return hashlib.sha512(m).digest()


def expandSK(sk):
    h = H(sk)
    a = 2 ** (b - 2) + sum(2 ** i * bit(h, i) for i in range(3, b - 2))
    k = b''.join([bytes([h[i]]) for i in range(b // 8, b // 4)])
    assert len(k) == 32
    return encodeint(a) + k


def onion_url_from_secret_key(secret_key):
    secret_key = nacl.signing.SigningKey(seed=secret_key)
    pubkey = bytes(secret_key.verify_key)
    version = b'\x03'
    checksum = hashlib.sha3_256(b".onion checksum" + pubkey + version).digest()[:2]
    onion_address = "http://{}.onion".format(base64.b32encode(pubkey + checksum + version).decode().lower())
    return onion_address


def generate_v3_secret_key():
    secretKey = os.urandom(32)
    expandedSecretKey = expandSK(secretKey)
    private_key = base64.b64encode(expandedSecretKey).decode()
    return (private_key, onion_url_from_secret_key(secretKey))

def generate_v2_secret_key():
    # Generate Onion Service key pair
    private_key = rsa.generate_private_key(public_exponent=65537,
                                           key_size=1024,
                                           backend=default_backend())
    hs_public_key = private_key.public_key()

    # Pre-generate Onion URL
    der_format = hs_public_key.public_bytes(encoding=serialization.Encoding.DER,
                                            format=serialization.PublicFormat.PKCS1)

    onion_url = base64.b32encode(hashlib.sha1(der_format).digest()[:-10]).lower().decode()


    # Generate Stem-compatible key content
    pem_format = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                           format=serialization.PrivateFormat.TraditionalOpenSSL,
                                           encryption_algorithm=serialization.NoEncryption())
    serialized_key = ''.join(pem_format.decode().split('\n')[1:-2])

    return (serialized_key, onion_url)
