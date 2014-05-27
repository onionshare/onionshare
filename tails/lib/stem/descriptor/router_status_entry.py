# Copyright 2012-2013, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Parsing for router status entries, the information for individual routers
within a network status document. This information is provided from a few
sources...

* control port via 'GETINFO ns/\*' and 'GETINFO md/\*' queries
* router entries in a network status document, like the cached-consensus

**Module Overview:**

::

  RouterStatusEntry - Common parent for router status entries
    |- RouterStatusEntryV2 - Entry for a network status v2 document
    |- RouterStatusEntryV3 - Entry for a network status v3 document
    +- RouterStatusEntryMicroV3 - Entry for a microdescriptor flavored v3 document
"""

import base64
import binascii
import datetime

import stem.exit_policy
import stem.util.str_tools

from stem.descriptor import (
  KEYWORD_LINE,
  Descriptor,
  _get_descriptor_components,
  _read_until_keywords,
)


def _parse_file(document_file, validate, entry_class, entry_keyword = "r", start_position = None, end_position = None, section_end_keywords = (), extra_args = ()):
  """
  Reads a range of the document_file containing some number of entry_class
  instances. We deliminate the entry_class entries by the keyword on their
  first line (entry_keyword). When finished the document is left at the
  end_position.

  Either an end_position or section_end_keywords must be provided.

  :param file document_file: file with network status document content
  :param bool validate: checks the validity of the document's contents if
    **True**, skips these checks otherwise
  :param class entry_class: class to construct instance for
  :param str entry_keyword: first keyword for the entry instances
  :param int start_position: start of the section, default is the current position
  :param int end_position: end of the section
  :param tuple section_end_keywords: keyword(s) that deliminate the end of the
    section if no end_position was provided
  :param tuple extra_args: extra arguments for the entry_class (after the
    content and validate flag)

  :returns: iterator over entry_class instances

  :raises:
    * **ValueError** if the contents is malformed and validate is **True**
    * **IOError** if the file can't be read
  """

  if start_position:
    document_file.seek(start_position)
  else:
    start_position = document_file.tell()

  # check if we're starting at the end of the section (ie, there's no entries to read)
  if section_end_keywords:
    first_keyword = None
    line_match = KEYWORD_LINE.match(stem.util.str_tools._to_unicode(document_file.readline()))

    if line_match:
      first_keyword = line_match.groups()[0]

    document_file.seek(start_position)

    if first_keyword in section_end_keywords:
      return

  while end_position is None or document_file.tell() < end_position:
    desc_lines, ending_keyword = _read_until_keywords(
      (entry_keyword,) + section_end_keywords,
      document_file,
      ignore_first = True,
      end_position = end_position,
      include_ending_keyword = True
    )

    desc_content = bytes.join(b"", desc_lines)

    if desc_content:
      yield entry_class(desc_content, validate, *extra_args)

      # check if we stopped at the end of the section
      if ending_keyword in section_end_keywords:
        break
    else:
      break


class RouterStatusEntry(Descriptor):
  """
  Information about an individual router stored within a network status
  document. This is the common parent for concrete status entry types.

  :var stem.descriptor.networkstatus.NetworkStatusDocument document: **\*** document that this descriptor came from

  :var str nickname: **\*** router's nickname
  :var str fingerprint: **\*** router's fingerprint
  :var datetime published: **\*** router's publication
  :var str address: **\*** router's IP address
  :var int or_port: **\*** router's ORPort
  :var int dir_port: **\*** router's DirPort

  :var list flags: **\*** list of :data:`~stem.Flag` associated with the relay

  :var stem.version.Version version: parsed version of tor, this is **None** if
    the relay's using a new versioning scheme
  :var str version_line: versioning information reported by the relay
  """

  def __init__(self, content, validate, document):
    """
    Parse a router descriptor in a network status document.

    :param str content: router descriptor content to be parsed
    :param NetworkStatusDocument document: document this descriptor came from
    :param bool validate: checks the validity of the content if **True**, skips
      these checks otherwise

    :raises: **ValueError** if the descriptor data is invalid
    """

    super(RouterStatusEntry, self).__init__(content)
    content = stem.util.str_tools._to_unicode(content)

    self.document = document

    self.nickname = None
    self.fingerprint = None
    self.published = None
    self.address = None
    self.or_port = None
    self.dir_port = None

    self.flags = None

    self.version_line = None
    self.version = None

    self._unrecognized_lines = []

    entries = _get_descriptor_components(content, validate)

    if validate:
      self._check_constraints(entries)

    self._parse(entries, validate)

  def _parse(self, entries, validate):
    """
    Parses the given content and applies the attributes.

    :param dict entries: keyword => (value, pgp key) entries
    :param bool validate: checks validity if **True**

    :raises: **ValueError** if a validity check fails
    """

    for keyword, values in entries.items():
      value, _ = values[0]

      if keyword == 's':
        _parse_s_line(self, value, validate)
      elif keyword == 'v':
        _parse_v_line(self, value, validate)
      else:
        self._unrecognized_lines.append("%s %s" % (keyword, value))

  def _check_constraints(self, entries):
    """
    Does a basic check that the entries conform to this descriptor type's
    constraints.

    :param dict entries: keyword => (value, pgp key) entries

    :raises: **ValueError** if an issue arises in validation
    """

    for keyword in self._required_fields():
      if not keyword in entries:
        raise ValueError("%s must have a '%s' line:\n%s" % (self._name(True), keyword, str(self)))

    for keyword in self._single_fields():
      if keyword in entries and len(entries[keyword]) > 1:
        raise ValueError("%s can only have a single '%s' line, got %i:\n%s" % (self._name(True), keyword, len(entries[keyword]), str(self)))

    if 'r' != entries.keys()[0]:
      raise ValueError("%s are expected to start with a 'r' line:\n%s" % (self._name(True), str(self)))

  def _name(self, is_plural = False):
    """
    Name for this descriptor type.
    """

    if is_plural:
      return "Router status entries"
    else:
      return "Router status entry"

  def _required_fields(self):
    """
    Provides lines that must appear in the descriptor.
    """

    return ()

  def _single_fields(self):
    """
    Provides lines that can only appear in the descriptor once.
    """

    return ()

  def get_unrecognized_lines(self):
    """
    Provides any unrecognized lines.

    :returns: list of unrecognized lines
    """

    return list(self._unrecognized_lines)

  def _compare(self, other, method):
    if not isinstance(other, RouterStatusEntry):
      return False

    return method(str(self).strip(), str(other).strip())

  def __eq__(self, other):
    return self._compare(other, lambda s, o: s == o)

  def __lt__(self, other):
    return self._compare(other, lambda s, o: s < o)

  def __le__(self, other):
    return self._compare(other, lambda s, o: s <= o)


class RouterStatusEntryV2(RouterStatusEntry):
  """
  Information about an individual router stored within a version 2 network
  status document.

  :var str digest: **\*** router's upper-case hex digest

  **\*** attribute is either required when we're parsed with validation or has
  a default value, others are left as **None** if undefined
  """

  def __init__(self, content, validate = True, document = None):
    self.digest = None
    super(RouterStatusEntryV2, self).__init__(content, validate, document)

  def _parse(self, entries, validate):
    for keyword, values in entries.items():
      value, _ = values[0]

      if keyword == 'r':
        _parse_r_line(self, value, validate, True)
        del entries['r']

    RouterStatusEntry._parse(self, entries, validate)

  def _name(self, is_plural = False):
    if is_plural:
      return "Router status entries (v2)"
    else:
      return "Router status entry (v2)"

  def _required_fields(self):
    return ('r')

  def _single_fields(self):
    return ('r', 's', 'v')

  def _compare(self, other, method):
    if not isinstance(other, RouterStatusEntryV2):
      return False

    return method(str(self).strip(), str(other).strip())

  def __eq__(self, other):
    return self._compare(other, lambda s, o: s == o)

  def __lt__(self, other):
    return self._compare(other, lambda s, o: s < o)

  def __le__(self, other):
    return self._compare(other, lambda s, o: s <= o)


class RouterStatusEntryV3(RouterStatusEntry):
  """
  Information about an individual router stored within a version 3 network
  status document.

  :var list or_addresses: **\*** relay's OR addresses, this is a tuple listing
    of the form (address (**str**), port (**int**), is_ipv6 (**bool**))
  :var str digest: **\*** router's upper-case hex digest

  :var int bandwidth: bandwidth claimed by the relay (in kb/s)
  :var int measured: bandwidth measured to be available by the relay
  :var bool is_unmeasured: bandwidth measurement isn't based on three or more
    measurements
  :var list unrecognized_bandwidth_entries: **\*** bandwidth weighting
    information that isn't yet recognized

  :var stem.exit_policy.MicroExitPolicy exit_policy: router's exit policy

  :var list microdescriptor_hashes: **\*** tuples of two values, the list of
    consensus methods for generating a set of digests and the 'algorithm =>
    digest' mappings

  **\*** attribute is either required when we're parsed with validation or has
  a default value, others are left as **None** if undefined
  """

  def __init__(self, content, validate = True, document = None):
    self.or_addresses = []
    self.digest = None

    self.bandwidth = None
    self.measured = None
    self.is_unmeasured = False
    self.unrecognized_bandwidth_entries = []

    self.exit_policy = None
    self.microdescriptor_hashes = []

    super(RouterStatusEntryV3, self).__init__(content, validate, document)

  def _parse(self, entries, validate):
    for keyword, values in entries.items():
      value, _ = values[0]

      if keyword == 'r':
        _parse_r_line(self, value, validate, True)
        del entries['r']
      elif keyword == 'a':
        for entry, _ in values:
          _parse_a_line(self, entry, validate)

        del entries['a']
      elif keyword == 'w':
        _parse_w_line(self, value, validate)
        del entries['w']
      elif keyword == 'p':
        _parse_p_line(self, value, validate)
        del entries['p']
      elif keyword == 'm':
        for entry, _ in values:
          _parse_m_line(self, entry, validate)

        del entries['m']

    RouterStatusEntry._parse(self, entries, validate)

  def _name(self, is_plural = False):
    if is_plural:
      return "Router status entries (v3)"
    else:
      return "Router status entry (v3)"

  def _required_fields(self):
    return ('r', 's')

  def _single_fields(self):
    return ('r', 's', 'v', 'w', 'p')

  def _compare(self, other, method):
    if not isinstance(other, RouterStatusEntryV3):
      return False

    return method(str(self).strip(), str(other).strip())

  def __eq__(self, other):
    return self._compare(other, lambda s, o: s == o)

  def __lt__(self, other):
    return self._compare(other, lambda s, o: s < o)

  def __le__(self, other):
    return self._compare(other, lambda s, o: s <= o)


class RouterStatusEntryMicroV3(RouterStatusEntry):
  """
  Information about an individual router stored within a microdescriptor
  flavored network status document.

  :var int bandwidth: bandwidth claimed by the relay (in kb/s)
  :var int measured: bandwidth measured to be available by the relay
  :var bool is_unmeasured: bandwidth measurement isn't based on three or more
    measurements
  :var list unrecognized_bandwidth_entries: **\*** bandwidth weighting
    information that isn't yet recognized

  :var str digest: **\*** router's hex encoded digest of our corresponding microdescriptor

  **\*** attribute is either required when we're parsed with validation or has
  a default value, others are left as **None** if undefined
  """

  def __init__(self, content, validate = True, document = None):
    self.bandwidth = None
    self.measured = None
    self.is_unmeasured = False
    self.unrecognized_bandwidth_entries = []

    self.digest = None

    super(RouterStatusEntryMicroV3, self).__init__(content, validate, document)

  def _parse(self, entries, validate):
    for keyword, values in entries.items():
      value, _ = values[0]

      if keyword == 'r':
        _parse_r_line(self, value, validate, False)
        del entries['r']
      elif keyword == 'w':
        _parse_w_line(self, value, validate)
        del entries['w']
      elif keyword == 'm':
        # "m" digest
        # example: m aiUklwBrua82obG5AsTX+iEpkjQA2+AQHxZ7GwMfY70

        self.digest = _base64_to_hex(value, validate, False)
        del entries['m']

    RouterStatusEntry._parse(self, entries, validate)

  def _name(self, is_plural = False):
    if is_plural:
      return "Router status entries (micro v3)"
    else:
      return "Router status entry (micro v3)"

  def _required_fields(self):
    return ('r', 's', 'm')

  def _single_fields(self):
    return ('r', 's', 'v', 'w', 'm')

  def _compare(self, other, method):
    if not isinstance(other, RouterStatusEntryMicroV3):
      return False

    return method(str(self).strip(), str(other).strip())

  def __eq__(self, other):
    return self._compare(other, lambda s, o: s == o)

  def __lt__(self, other):
    return self._compare(other, lambda s, o: s < o)

  def __le__(self, other):
    return self._compare(other, lambda s, o: s <= o)


def _parse_r_line(desc, value, validate, include_digest = True):
  # Parses a RouterStatusEntry's 'r' line. They're very nearly identical for
  # all current entry types (v2, v3, and microdescriptor v3) with one little
  # wrinkle: only the microdescriptor flavor excludes a 'digest' field.
  #
  # For v2 and v3 router status entries:
  #   "r" nickname identity digest publication IP ORPort DirPort
  #   example: r mauer BD7xbfsCFku3+tgybEZsg8Yjhvw itcuKQ6PuPLJ7m/Oi928WjO2j8g 2012-06-22 13:19:32 80.101.105.103 9001 0
  #
  # For v3 microdescriptor router status entries:
  #   "r" nickname identity publication IP ORPort DirPort
  #   example: r Konata ARIJF2zbqirB9IwsW0mQznccWww 2012-09-24 13:40:40 69.64.48.168 9001 9030

  r_comp = value.split(" ")

  # inject a None for the digest to normalize the field positioning
  if not include_digest:
    r_comp.insert(2, None)

  if len(r_comp) < 8:
    if not validate:
      return

    expected_field_count = 'eight' if include_digest else 'seven'
    raise ValueError("%s 'r' line must have %s values: r %s" % (desc._name(), expected_field_count, value))

  if validate:
    if not stem.util.tor_tools.is_valid_nickname(r_comp[0]):
      raise ValueError("%s nickname isn't valid: %s" % (desc._name(), r_comp[0]))
    elif not stem.util.connection.is_valid_ipv4_address(r_comp[5]):
      raise ValueError("%s address isn't a valid IPv4 address: %s" % (desc._name(), r_comp[5]))
    elif not stem.util.connection.is_valid_port(r_comp[6]):
      raise ValueError("%s ORPort is invalid: %s" % (desc._name(), r_comp[6]))
    elif not stem.util.connection.is_valid_port(r_comp[7], allow_zero = True):
      raise ValueError("%s DirPort is invalid: %s" % (desc._name(), r_comp[7]))
  elif not (r_comp[6].isdigit() and r_comp[7].isdigit()):
    return

  desc.nickname = r_comp[0]
  desc.fingerprint = _base64_to_hex(r_comp[1], validate)

  if include_digest:
    desc.digest = _base64_to_hex(r_comp[2], validate)

  desc.address = r_comp[5]
  desc.or_port = int(r_comp[6])
  desc.dir_port = None if r_comp[7] == '0' else int(r_comp[7])

  try:
    published = "%s %s" % (r_comp[3], r_comp[4])
    desc.published = datetime.datetime.strptime(published, "%Y-%m-%d %H:%M:%S")
  except ValueError:
    if validate:
      raise ValueError("Publication time time wasn't parsable: r %s" % value)


def _parse_a_line(desc, value, validate):
  # "a" SP address ":" portlist
  # example: a [2001:888:2133:0:82:94:251:204]:9001

  if not ':' in value:
    if not validate:
      return

    raise ValueError("%s 'a' line must be of the form '[address]:[ports]': a %s" % (desc._name(), value))

  address, port = value.rsplit(':', 1)
  is_ipv6 = address.startswith("[") and address.endswith("]")

  if is_ipv6:
    address = address[1:-1]  # remove brackets

  if not ((not is_ipv6 and stem.util.connection.is_valid_ipv4_address(address)) or
          (is_ipv6 and stem.util.connection.is_valid_ipv6_address(address))):
    if not validate:
      return
    else:
      raise ValueError("%s 'a' line must start with an IPv6 address: a %s" % (desc._name(), value))

  if stem.util.connection.is_valid_port(port):
    desc.or_addresses.append((address, int(port), is_ipv6))
  elif validate:
    raise ValueError("%s 'a' line had an invalid port (%s): a %s" % (desc._name(), port, value))


def _parse_s_line(desc, value, validate):
  # "s" Flags
  # example: s Named Running Stable Valid

  flags = [] if value == "" else value.split(" ")
  desc.flags = flags

  if validate:
    for flag in flags:
      if flags.count(flag) > 1:
        raise ValueError("%s had duplicate flags: s %s" % (desc._name(), value))
      elif flag == "":
        raise ValueError("%s had extra whitespace on its 's' line: s %s" % (desc._name(), value))


def _parse_v_line(desc, value, validate):
  # "v" version
  # example: v Tor 0.2.2.35
  #
  # The spec says that if this starts with "Tor " then what follows is a
  # tor version. If not then it has "upgraded to a more sophisticated
  # protocol versioning system".

  desc.version_line = value

  if value.startswith("Tor "):
    try:
      desc.version = stem.version._get_version(value[4:])
    except ValueError as exc:
      if validate:
        raise ValueError("%s has a malformed tor version (%s): v %s" % (desc._name(), exc, value))


def _parse_w_line(desc, value, validate):
  # "w" "Bandwidth=" INT ["Measured=" INT] ["Unmeasured=1"]
  # example: w Bandwidth=7980

  w_comp = value.split(" ")

  if len(w_comp) < 1:
    if not validate:
      return

    raise ValueError("%s 'w' line is blank: w %s" % (desc._name(), value))
  elif not w_comp[0].startswith("Bandwidth="):
    if not validate:
      return

    raise ValueError("%s 'w' line needs to start with a 'Bandwidth=' entry: w %s" % (desc._name(), value))

  for w_entry in w_comp:
    if '=' in w_entry:
      w_key, w_value = w_entry.split('=', 1)
    else:
      w_key, w_value = w_entry, None

    if w_key == "Bandwidth":
      if not (w_value and w_value.isdigit()):
        if not validate:
          return

        raise ValueError("%s 'Bandwidth=' entry needs to have a numeric value: w %s" % (desc._name(), value))

      desc.bandwidth = int(w_value)
    elif w_key == "Measured":
      if not (w_value and w_value.isdigit()):
        if not validate:
          return

        raise ValueError("%s 'Measured=' entry needs to have a numeric value: w %s" % (desc._name(), value))

      desc.measured = int(w_value)
    elif w_key == "Unmeasured":
      if validate and w_value != "1":
        raise ValueError("%s 'Unmeasured=' should only have the value of '1': w %s" % (desc._name(), value))

      desc.is_unmeasured = True
    else:
      desc.unrecognized_bandwidth_entries.append(w_entry)


def _parse_p_line(desc, value, validate):
  # "p" ("accept" / "reject") PortList
  # p reject 1-65535
  # example: p accept 80,110,143,443,993,995,6660-6669,6697,7000-7001

  try:
    desc.exit_policy = stem.exit_policy.MicroExitPolicy(value)
  except ValueError as exc:
    if not validate:
      return

    raise ValueError("%s exit policy is malformed (%s): p %s" % (desc._name(), exc, value))


def _parse_m_line(desc, value, validate):
  # "m" methods 1*(algorithm "=" digest)
  # example: m 8,9,10,11,12 sha256=g1vx9si329muxV3tquWIXXySNOIwRGMeAESKs/v4DWs

  m_comp = value.split(" ")

  if not (desc.document and desc.document.is_vote):
    if not validate:
      return

    vote_status = "vote" if desc.document else "<undefined document>"
    raise ValueError("%s 'm' line should only appear in votes (appeared in a %s): m %s" % (desc._name(), vote_status, value))
  elif len(m_comp) < 1:
    if not validate:
      return

    raise ValueError("%s 'm' line needs to start with a series of methods: m %s" % (desc._name(), value))

  try:
    methods = [int(entry) for entry in m_comp[0].split(",")]
  except ValueError:
    if not validate:
      return

    raise ValueError("%s microdescriptor methods should be a series of comma separated integers: m %s" % (desc._name(), value))

  hashes = {}

  for entry in m_comp[1:]:
    if not '=' in entry:
      if not validate:
        continue

      raise ValueError("%s can only have a series of 'algorithm=digest' mappings after the methods: m %s" % (desc._name(), value))

    hash_name, digest = entry.split('=', 1)
    hashes[hash_name] = digest

  desc.microdescriptor_hashes.append((methods, hashes))


def _base64_to_hex(identity, validate, check_if_fingerprint = True):
  """
  Decodes a base64 value to hex. For example...

  ::

    >>> _base64_to_hex('p1aag7VwarGxqctS7/fS0y5FU+s')
    'A7569A83B5706AB1B1A9CB52EFF7D2D32E4553EB'

  :param str identity: encoded fingerprint from the consensus
  :param bool validate: checks validity if **True**
  :param bool check_if_fingerprint: asserts that the result is a fingerprint if **True**

  :returns: **str** with the uppercase hex encoding of the relay's fingerprint

  :raises: **ValueError** if the result isn't a valid fingerprint
  """

  # trailing equal signs were stripped from the identity
  missing_padding = len(identity) % 4
  identity += "=" * missing_padding

  fingerprint = ""

  try:
    identity_decoded = base64.b64decode(stem.util.str_tools._to_bytes(identity))
  except (TypeError, binascii.Error):
    if not validate:
      return None

    raise ValueError("Unable to decode identity string '%s'" % identity)

  for char in identity_decoded:
    # Individual characters are either standard ASCII or hex encoded, and each
    # represent two hex digits. For instance...
    #
    # >>> ord('\n')
    # 10
    # >>> hex(10)
    # '0xa'
    # >>> '0xa'[2:].zfill(2).upper()
    # '0A'

    char_int = char if isinstance(char, int) else ord(char)
    fingerprint += hex(char_int)[2:].zfill(2).upper()

  if check_if_fingerprint:
    if not stem.util.tor_tools.is_valid_fingerprint(fingerprint):
      if not validate:
        return None

      raise ValueError("Decoded '%s' to be '%s', which isn't a valid fingerprint" % (identity, fingerprint))

  return fingerprint
