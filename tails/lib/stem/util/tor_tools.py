# Copyright 2012-2013, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Miscellaneous utility functions for working with tor.

**These functions are not being vended to stem users. They may change in the
future, use them at your own risk.**

**Module Overview:**

::

  is_valid_fingerprint - checks if a string is a valid tor relay fingerprint
  is_valid_nickname - checks if a string is a valid tor relay nickname
  is_valid_circuit_id - checks if a string is a valid tor circuit id
  is_valid_stream_id - checks if a string is a valid tor stream id
  is_hex_digits - checks if a string is only made up of hex digits
"""

import re

# The control-spec defines the following as...
#
#   Fingerprint = "$" 40*HEXDIG
#   NicknameChar = "a"-"z" / "A"-"Z" / "0" - "9"
#   Nickname = 1*19 NicknameChar
#
#   CircuitID = 1*16 IDChar
#   IDChar = ALPHA / DIGIT
#
# HEXDIG is defined in RFC 5234 as being uppercase and used in RFC 5987 as
# case insensitive. Tor doesn't define this in the spec so flipping a coin
# and going with case insensitive.

HEX_DIGIT = "[0-9a-fA-F]"
FINGERPRINT_PATTERN = re.compile("^%s{40}$" % HEX_DIGIT)
NICKNAME_PATTERN = re.compile("^[a-zA-Z0-9]{1,19}$")
CIRC_ID_PATTERN = re.compile("^[a-zA-Z0-9]{1,16}$")


def is_valid_fingerprint(entry, check_prefix = False):
  """
  Checks if a string is a properly formatted relay fingerprint. This checks for
  a '$' prefix if check_prefix is true, otherwise this only validates the hex
  digits.

  :param str entry: string to be checked
  :param bool check_prefix: checks for a '$' prefix

  :returns: **True** if the string could be a relay fingerprint, **False** otherwise
  """

  if not isinstance(entry, (str, unicode)):
    return False
  elif check_prefix:
    if not entry or entry[0] != "$":
      return False

    entry = entry[1:]

  return bool(FINGERPRINT_PATTERN.match(entry))


def is_valid_nickname(entry):
  """
  Checks if a string is a valid format for being a nickname.

  :param str entry: string to be checked

  :returns: **True** if the string could be a nickname, **False** otherwise
  """

  if not isinstance(entry, (str, unicode)):
    return False

  return bool(NICKNAME_PATTERN.match(entry))


def is_valid_circuit_id(entry):
  """
  Checks if a string is a valid format for being a circuit identifier.

  :returns: **True** if the string could be a circuit id, **False** otherwise
  """

  if not isinstance(entry, (str, unicode)):
    return False

  return bool(CIRC_ID_PATTERN.match(entry))


def is_valid_stream_id(entry):
  """
  Checks if a string is a valid format for being a stream identifier.
  Currently, this is just an alias to :func:`~stem.util.tor_tools.is_valid_circuit_id`.

  :returns: **True** if the string could be a stream id, **False** otherwise
  """

  return is_valid_circuit_id(entry)


def is_hex_digits(entry, count):
  """
  Checks if a string is the given number of hex digits. Digits represented by
  letters are case insensitive.

  :param str entry: string to be checked
  :param int count: number of hex digits to be checked for

  :returns: **True** if the string matches this number
  """

  return bool(re.match("^%s{%i}$" % (HEX_DIGIT, count), entry))
