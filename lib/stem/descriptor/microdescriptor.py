# Copyright 2013, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Parsing for Tor microdescriptors, which contain a distilled version of a
relay's server descriptor. As of Tor version 0.2.3.3-alpha Tor no longer
downloads server descriptors by default, opting for microdescriptors instead.

Unlike most descriptor documents these aren't available on the metrics site
(since they don't contain any information that the server descriptors don't).

The limited information in microdescriptors make them rather clunky to use
compared with server descriptors. For instance microdescriptors lack the
relay's fingerprint, making it difficut to use them to look up the relay's
other descriptors.

To do so you need to match the microdescriptor's digest against its
corresponding router status entry. For added fun as of this writing the
controller doesn't even surface those router status entries
(:trac:`7953`).

For instance, here's an example that prints the nickname and fignerprints of
the exit relays.

::

  import os

  from stem.control import Controller
  from stem.descriptor import parse_file

  with Controller.from_port(port = 9051) as controller:
    controller.authenticate()

    exit_digests = set()
    data_dir = controller.get_conf("DataDirectory")

    for desc in controller.get_microdescriptors():
      if desc.exit_policy.is_exiting_allowed():
        exit_digests.add(desc.digest)

    print "Exit Relays:"

    for desc in parse_file(os.path.join(data_dir, 'cached-microdesc-consensus')):
      if desc.digest in exit_digests:
        print "  %s (%s)" % (desc.nickname, desc.fingerprint)

Doing the same is trivial with server descriptors...

::

  from stem.descriptor import parse_file

  print "Exit Relays:"

  for desc in parse_file("/home/atagar/.tor/cached-descriptors"):
    if desc.exit_policy.is_exiting_allowed():
      print "  %s (%s)" % (desc.nickname, desc.fingerprint)

**Module Overview:**

::

  Microdescriptor - Tor microdescriptor.
"""

import hashlib

import stem.descriptor.router_status_entry
import stem.exit_policy

from stem.descriptor import (
  Descriptor,
  _get_descriptor_components,
  _read_until_keywords,
)

try:
  # added in python 3.2
  from functools import lru_cache
except ImportError:
  from stem.util.lru_cache import lru_cache

REQUIRED_FIELDS = (
  "onion-key",
)

SINGLE_FIELDS = (
  "onion-key",
  "ntor-onion-key",
  "family",
  "p",
  "p6",
)


def _parse_file(descriptor_file, validate = True, **kwargs):
  """
  Iterates over the microdescriptors in a file.

  :param file descriptor_file: file with descriptor content
  :param bool validate: checks the validity of the descriptor's content if
    **True**, skips these checks otherwise
  :param dict kwargs: additional arguments for the descriptor constructor

  :returns: iterator for Microdescriptor instances in the file

  :raises:
    * **ValueError** if the contents is malformed and validate is True
    * **IOError** if the file can't be read
  """

  while True:
    annotations = _read_until_keywords("onion-key", descriptor_file)

    # read until we reach an annotation or onion-key line
    descriptor_lines = []

    # read the onion-key line, done if we're at the end of the document

    onion_key_line = descriptor_file.readline()

    if onion_key_line:
      descriptor_lines.append(onion_key_line)
    else:
      break

    while True:
      last_position = descriptor_file.tell()
      line = descriptor_file.readline()

      if not line:
        break  # EOF
      elif line.startswith(b"@") or line.startswith(b"onion-key"):
        descriptor_file.seek(last_position)
        break
      else:
        descriptor_lines.append(line)

    if descriptor_lines:
      # strip newlines from annotations
      annotations = map(bytes.strip, annotations)

      descriptor_text = bytes.join(b"", descriptor_lines)

      yield Microdescriptor(descriptor_text, validate, annotations, **kwargs)
    else:
      break  # done parsing descriptors


class Microdescriptor(Descriptor):
  """
  Microdescriptor (`descriptor specification
  <https://gitweb.torproject.org/torspec.git/blob/HEAD:/dir-spec.txt>`_)

  :var str digest: **\*** hex digest for this microdescriptor, this can be used
    to match against the corresponding digest attribute of a
    :class:`~stem.descriptor.router_status_entry.RouterStatusEntryMicroV3`
  :var str onion_key: **\*** key used to encrypt EXTEND cells
  :var str ntor_onion_key: base64 key used to encrypt EXTEND in the ntor protocol
  :var list or_addresses: **\*** alternative for our address/or_port attributes, each
    entry is a tuple of the form (address (**str**), port (**int**), is_ipv6
    (**bool**))
  :var list family: **\*** nicknames or fingerprints of declared family
  :var stem.exit_policy.MicroExitPolicy exit_policy: **\*** relay's exit policy
  :var stem.exit_policy.MicroExitPolicy exit_policy_v6: **\*** exit policy for IPv6

  **\*** attribute is required when we're parsed with validation
  """

  def __init__(self, raw_contents, validate = True, annotations = None):
    super(Microdescriptor, self).__init__(raw_contents)
    raw_contents = stem.util.str_tools._to_unicode(raw_contents)

    self.digest = hashlib.sha256(self.get_bytes()).hexdigest().upper()

    self.onion_key = None
    self.ntor_onion_key = None
    self.or_addresses = []
    self.family = []
    self.exit_policy = stem.exit_policy.MicroExitPolicy("reject 1-65535")
    self.exit_policy_v6 = None

    self._unrecognized_lines = []

    self._annotation_lines = annotations if annotations else []

    entries = _get_descriptor_components(raw_contents, validate)
    self._parse(entries, validate)

    if validate:
      self._check_constraints(entries)

  def get_unrecognized_lines(self):
    return list(self._unrecognized_lines)

  @lru_cache()
  def get_annotations(self):
    """
    Provides content that appeared prior to the descriptor. If this comes from
    the cached-microdescs then this commonly contains content like...

    ::

      @last-listed 2013-02-24 00:18:30

    :returns: **dict** with the key/value pairs in our annotations
    """

    annotation_dict = {}

    for line in self._annotation_lines:
      if b" " in line:
        key, value = line.split(b" ", 1)
        annotation_dict[key] = value
      else:
        annotation_dict[line] = None

    return annotation_dict

  def get_annotation_lines(self):
    """
    Provides the lines of content that appeared prior to the descriptor. This
    is the same as the
    :func:`~stem.descriptor.microdescriptor.Microdescriptor.get_annotations`
    results, but with the unparsed lines and ordering retained.

    :returns: **list** with the lines of annotation that came before this descriptor
    """

    return self._annotation_lines

  def _parse(self, entries, validate):
    """
    Parses a series of 'keyword => (value, pgp block)' mappings and applies
    them as attributes.

    :param dict entries: descriptor contents to be applied
    :param bool validate: checks the validity of descriptor content if **True**

    :raises: **ValueError** if an error occurs in validation
    """

    for keyword, values in entries.items():
      # most just work with the first (and only) value
      value, block_contents = values[0]

      line = "%s %s" % (keyword, value)  # original line

      if block_contents:
        line += "\n%s" % block_contents

      if keyword == "onion-key":
        if validate and not block_contents:
          raise ValueError("Onion key line must be followed by a public key: %s" % line)

        self.onion_key = block_contents
      elif keyword == "ntor-onion-key":
        self.ntor_onion_key = value
      elif keyword == "a":
        for entry, _ in values:
          stem.descriptor.router_status_entry._parse_a_line(self, entry, validate)
      elif keyword == "family":
        self.family = value.split(" ")
      elif keyword == "p":
        stem.descriptor.router_status_entry._parse_p_line(self, value, validate)
      elif keyword == "p6":
        self.exit_policy_v6 = stem.exit_policy.MicroExitPolicy(value)
      else:
        self._unrecognized_lines.append(line)

  def _check_constraints(self, entries):
    """
    Does a basic check that the entries conform to this descriptor type's
    constraints.

    :param dict entries: keyword => (value, pgp key) entries

    :raises: **ValueError** if an issue arises in validation
    """

    for keyword in REQUIRED_FIELDS:
      if not keyword in entries:
        raise ValueError("Microdescriptor must have a '%s' entry" % keyword)

    for keyword in SINGLE_FIELDS:
      if keyword in entries and len(entries[keyword]) > 1:
        raise ValueError("The '%s' entry can only appear once in a microdescriptor" % keyword)

    if "onion-key" != entries.keys()[0]:
      raise ValueError("Microdescriptor must start with a 'onion-key' entry")

  def _compare(self, other, method):
    if not isinstance(other, Microdescriptor):
      return False

    return method(str(self).strip(), str(other).strip())

  def __hash__(self):
    return hash(str(self).strip())

  def __eq__(self, other):
    return self._compare(other, lambda s, o: s == o)

  def __lt__(self, other):
    return self._compare(other, lambda s, o: s < o)

  def __le__(self, other):
    return self._compare(other, lambda s, o: s <= o)
