# Copyright 2012-2013, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Package for parsing and processing descriptor data.

**Module Overview:**

::

  parse_file - Parses the descriptors in a file.

  Descriptor - Common parent for all descriptor file types.
    |- get_path - location of the descriptor on disk if it came from a file
    |- get_archive_path - location of the descriptor within the archive it came from
    |- get_bytes - similar to str(), but provides our original bytes content
    |- get_unrecognized_lines - unparsed descriptor content
    +- __str__ - string that the descriptor was made from

.. data:: DocumentHandler (enum)

  Ways in which we can parse a
  :class:`~stem.descriptor.networkstatus.NetworkStatusDocument`.

  Both **ENTRIES** and **BARE_DOCUMENT** have a 'thin' document, which doesn't
  have a populated **routers** attribute. This allows for lower memory usage
  and upfront runtime. However, if read time and memory aren't a concern then
  **DOCUMENT** can provide you with a fully populated document.

  =================== ===========
  DocumentHandler     Description
  =================== ===========
  **ENTRIES**         Iterates over the contained :class:`~stem.descriptor.router_status_entry.RouterStatusEntry`. Each has a reference to the bare document it came from (through its **document** attribute).
  **DOCUMENT**        :class:`~stem.descriptor.networkstatus.NetworkStatusDocument` with the :class:`~stem.descriptor.router_status_entry.RouterStatusEntry` it contains (through its **routers** attribute).
  **BARE_DOCUMENT**   :class:`~stem.descriptor.networkstatus.NetworkStatusDocument` **without** a reference to its contents (the :class:`~stem.descriptor.router_status_entry.RouterStatusEntry` are unread).
  =================== ===========
"""

__all__ = [
  "export",
  "reader",
  "remote",
  "extrainfo_descriptor",
  "server_descriptor",
  "microdescriptor",
  "networkstatus",
  "router_status_entry",
  "tordnsel",
  "parse_file",
  "Descriptor",
]

import os
import re

import stem.prereq
import stem.util.enum
import stem.util.str_tools

try:
  # added in python 2.7
  from collections import OrderedDict
except ImportError:
  from stem.util.ordereddict import OrderedDict

KEYWORD_CHAR = "a-zA-Z0-9-"
WHITESPACE = " \t"
KEYWORD_LINE = re.compile("^([%s]+)(?:[%s]+(.*))?$" % (KEYWORD_CHAR, WHITESPACE))
PGP_BLOCK_START = re.compile("^-----BEGIN ([%s%s]+)-----$" % (KEYWORD_CHAR, WHITESPACE))
PGP_BLOCK_END = "-----END %s-----"

DocumentHandler = stem.util.enum.UppercaseEnum(
  "ENTRIES",
  "DOCUMENT",
  "BARE_DOCUMENT",
)


def parse_file(descriptor_file, descriptor_type = None, validate = True, document_handler = DocumentHandler.ENTRIES, **kwargs):
  """
  Simple function to read the descriptor contents from a file, providing an
  iterator for its :class:`~stem.descriptor.__init__.Descriptor` contents.

  If you don't provide a **descriptor_type** argument then this automatically
  tries to determine the descriptor type based on the following...

  * The @type annotation on the first line. These are generally only found in
    the `descriptor archives <https://metrics.torproject.org>`_.

  * The filename if it matches something from tor's data directory. For
    instance, tor's 'cached-descriptors' contains server descriptors.

  This is a handy function for simple usage, but if you're reading multiple
  descriptor files you might want to consider the
  :class:`~stem.descriptor.reader.DescriptorReader`.

  Descriptor types include the following, including further minor versions (ie.
  if we support 1.1 then we also support everything from 1.0 and most things
  from 1.2, but not 2.0)...

  ========================================= =====
  Descriptor Type                           Class
  ========================================= =====
  server-descriptor 1.0                     :class:`~stem.descriptor.server_descriptor.RelayDescriptor`
  extra-info 1.0                            :class:`~stem.descriptor.extrainfo_descriptor.RelayExtraInfoDescriptor`
  microdescriptor 1.0                       :class:`~stem.descriptor.microdescriptor.Microdescriptor`
  directory 1.0                             **unsupported**
  network-status-2 1.0                      :class:`~stem.descriptor.router_status_entry.RouterStatusEntryV2` (with a :class:`~stem.descriptor.networkstatus.NetworkStatusDocumentV2`)
  dir-key-certificate-3 1.0                 :class:`~stem.descriptor.networkstatus.KeyCertificate`
  network-status-consensus-3 1.0            :class:`~stem.descriptor.router_status_entry.RouterStatusEntryV3` (with a :class:`~stem.descriptor.networkstatus.NetworkStatusDocumentV3`)
  network-status-vote-3 1.0                 :class:`~stem.descriptor.router_status_entry.RouterStatusEntryV3` (with a :class:`~stem.descriptor.networkstatus.NetworkStatusDocumentV3`)
  network-status-microdesc-consensus-3 1.0  :class:`~stem.descriptor.router_status_entry.RouterStatusEntryMicroV3` (with a :class:`~stem.descriptor.networkstatus.NetworkStatusDocumentV3`)
  bridge-network-status 1.0                 :class:`~stem.descriptor.router_status_entry.RouterStatusEntryV3` (with a :class:`~stem.descriptor.networkstatus.BridgeNetworkStatusDocument`)
  bridge-server-descriptor 1.0              :class:`~stem.descriptor.server_descriptor.BridgeDescriptor`
  bridge-extra-info 1.1                     :class:`~stem.descriptor.extrainfo_descriptor.BridgeExtraInfoDescriptor`
  torperf 1.0                               **unsupported**
  bridge-pool-assignment 1.0                **unsupported**
  tordnsel 1.0                              :class:`~stem.descriptor.tordnsel.TorDNSEL`
  ========================================= =====

  If you're using **python 3** then beware that the open() function defaults to
  using text mode. **Binary mode** is strongly suggested because it's both
  faster (by my testing by about 33x) and doesn't do universal newline
  translation which can make us misparse the document.

  ::

    my_descriptor_file = open(descriptor_path, 'rb')

  :param str,file descriptor_file: path or opened file with the descriptor contents
  :param str descriptor_type: `descriptor type <https://metrics.torproject.org/formats.html#descriptortypes>`_, this is guessed if not provided
  :param bool validate: checks the validity of the descriptor's content if
    **True**, skips these checks otherwise
  :param stem.descriptor.__init__.DocumentHandler document_handler: method in
    which to parse the :class:`~stem.descriptor.networkstatus.NetworkStatusDocument`
  :param dict kwargs: additional arguments for the descriptor constructor

  :returns: iterator for :class:`~stem.descriptor.__init__.Descriptor` instances in the file

  :raises:
    * **ValueError** if the contents is malformed and validate is True
    * **TypeError** if we can't match the contents of the file to a descriptor type
    * **IOError** if unable to read from the descriptor_file
  """

  # if we got a path then open that file for parsing

  if isinstance(descriptor_file, (bytes, unicode)):
    with open(descriptor_file) as desc_file:
      for desc in parse_file(desc_file, descriptor_type, validate, document_handler, **kwargs):
        yield desc

      return

  # The tor descriptor specifications do not provide a reliable method for
  # identifying a descriptor file's type and version so we need to guess
  # based on its filename. Metrics descriptors, however, can be identified
  # by an annotation on their first line...
  # https://trac.torproject.org/5651

  initial_position = descriptor_file.tell()
  first_line = stem.util.str_tools._to_unicode(descriptor_file.readline().strip())
  metrics_header_match = re.match("^@type (\S+) (\d+).(\d+)$", first_line)

  if not metrics_header_match:
    descriptor_file.seek(initial_position)

  descriptor_path = getattr(descriptor_file, 'name', None)
  filename = '<undefined>' if descriptor_path is None else os.path.basename(descriptor_file.name)
  file_parser = None

  if descriptor_type is not None:
    descriptor_type_match = re.match("^(\S+) (\d+).(\d+)$", descriptor_type)

    if descriptor_type_match:
      desc_type, major_version, minor_version = descriptor_type_match.groups()
      file_parser = lambda f: _parse_metrics_file(desc_type, int(major_version), int(minor_version), f, validate, document_handler, **kwargs)
    else:
      raise ValueError("The descriptor_type must be of the form '<type> <major_version>.<minor_version>'")
  elif metrics_header_match:
    # Metrics descriptor handling

    desc_type, major_version, minor_version = metrics_header_match.groups()
    file_parser = lambda f: _parse_metrics_file(desc_type, int(major_version), int(minor_version), f, validate, document_handler, **kwargs)
  else:
    # Cached descriptor handling. These contain multiple descriptors per file.

    if filename == "cached-descriptors":
      file_parser = lambda f: stem.descriptor.server_descriptor._parse_file(f, validate = validate, **kwargs)
    elif filename == "cached-extrainfo":
      file_parser = lambda f: stem.descriptor.extrainfo_descriptor._parse_file(f, validate = validate, **kwargs)
    elif filename == "cached-microdescs":
      file_parser = lambda f: stem.descriptor.microdescriptor._parse_file(f, validate = validate, **kwargs)
    elif filename == "cached-consensus":
      file_parser = lambda f: stem.descriptor.networkstatus._parse_file(f, validate = validate, document_handler = document_handler, **kwargs)
    elif filename == "cached-microdesc-consensus":
      file_parser = lambda f: stem.descriptor.networkstatus._parse_file(f, is_microdescriptor = True, validate = validate, document_handler = document_handler, **kwargs)

  if file_parser:
    for desc in file_parser(descriptor_file):
      if descriptor_path is not None:
        desc._set_path(os.path.abspath(descriptor_path))

      yield desc

    return

  # Not recognized as a descriptor file.

  raise TypeError("Unable to determine the descriptor's type. filename: '%s', first line: '%s'" % (filename, first_line))


def _parse_metrics_file(descriptor_type, major_version, minor_version, descriptor_file, validate, document_handler, **kwargs):
  # Parses descriptor files from metrics, yielding individual descriptors. This
  # throws a TypeError if the descriptor_type or version isn't recognized.

  if descriptor_type == "server-descriptor" and major_version == 1:
    for desc in stem.descriptor.server_descriptor._parse_file(descriptor_file, is_bridge = False, validate = validate, **kwargs):
      yield desc
  elif descriptor_type == "bridge-server-descriptor" and major_version == 1:
    for desc in stem.descriptor.server_descriptor._parse_file(descriptor_file, is_bridge = True, validate = validate, **kwargs):
      yield desc
  elif descriptor_type == "extra-info" and major_version == 1:
    for desc in stem.descriptor.extrainfo_descriptor._parse_file(descriptor_file, is_bridge = False, validate = validate, **kwargs):
      yield desc
  elif descriptor_type == "microdescriptor" and major_version == 1:
    for desc in stem.descriptor.microdescriptor._parse_file(descriptor_file, validate = validate, **kwargs):
      yield desc
  elif descriptor_type == "bridge-extra-info" and major_version == 1:
    # version 1.1 introduced a 'transport' field...
    # https://trac.torproject.org/6257

    for desc in stem.descriptor.extrainfo_descriptor._parse_file(descriptor_file, is_bridge = True, validate = validate, **kwargs):
      yield desc
  elif descriptor_type == "network-status-2" and major_version == 1:
    document_type = stem.descriptor.networkstatus.NetworkStatusDocumentV2

    for desc in stem.descriptor.networkstatus._parse_file(descriptor_file, document_type, validate = validate, document_handler = document_handler, **kwargs):
      yield desc
  elif descriptor_type == "dir-key-certificate-3" and major_version == 1:
    for desc in stem.descriptor.networkstatus._parse_file_key_certs(descriptor_file, validate = validate, **kwargs):
      yield desc
  elif descriptor_type in ("network-status-consensus-3", "network-status-vote-3") and major_version == 1:
    document_type = stem.descriptor.networkstatus.NetworkStatusDocumentV3

    for desc in stem.descriptor.networkstatus._parse_file(descriptor_file, document_type, validate = validate, document_handler = document_handler, **kwargs):
      yield desc
  elif descriptor_type == "network-status-microdesc-consensus-3" and major_version == 1:
    document_type = stem.descriptor.networkstatus.NetworkStatusDocumentV3

    for desc in stem.descriptor.networkstatus._parse_file(descriptor_file, document_type, is_microdescriptor = True, validate = validate, document_handler = document_handler, **kwargs):
      yield desc
  elif descriptor_type == "bridge-network-status" and major_version == 1:
    document_type = stem.descriptor.networkstatus.BridgeNetworkStatusDocument

    for desc in stem.descriptor.networkstatus._parse_file(descriptor_file, document_type, validate = validate, document_handler = document_handler, **kwargs):
      yield desc
  elif descriptor_type == "tordnsel" and major_version == 1:
    document_type = stem.descriptor.tordnsel.TorDNSEL

    for desc in stem.descriptor.tordnsel._parse_file(descriptor_file, validate = validate, **kwargs):
      yield desc
  else:
    raise TypeError("Unrecognized metrics descriptor format. type: '%s', version: '%i.%i'" % (descriptor_type, major_version, minor_version))


class Descriptor(object):
  """
  Common parent for all types of descriptors.
  """

  def __init__(self, contents):
    self._path = None
    self._archive_path = None
    self._raw_contents = contents

  def get_path(self):
    """
    Provides the absolute path that we loaded this descriptor from.

    :returns: **str** with the absolute path of the descriptor source
    """

    return self._path

  def get_archive_path(self):
    """
    If this descriptor came from an archive then provides its path within the
    archive. This is only set if the descriptor came from a
    :class:`~stem.descriptor.reader.DescriptorReader`, and is **None** if this
    descriptor didn't come from an archive.

    :returns: **str** with the descriptor's path within the archive
    """

    return self._archive_path

  def get_bytes(self):
    """
    Provides the ASCII **bytes** of the descriptor. This only differs from
    **str()** if you're running python 3.x, in which case **str()** provides a
    **unicode** string.

    :returns: **bytes** for the descriptor's contents
    """

    return self._raw_contents

  def get_unrecognized_lines(self):
    """
    Provides a list of lines that were either ignored or had data that we did
    not know how to process. This is most common due to new descriptor fields
    that this library does not yet know how to process. Patches welcome!

    :returns: **list** of lines of unrecognized content
    """

    raise NotImplementedError

  def _set_path(self, path):
    self._path = path

  def _set_archive_path(self, path):
    self._archive_path = path

  def __str__(self):
    if stem.prereq.is_python_3():
      return stem.util.str_tools._to_unicode(self._raw_contents)
    else:
      return self._raw_contents


def _get_bytes_field(keyword, content):
  """
  Provides the value corresponding to the given keyword. This is handy to fetch
  values specifically allowed to be arbitrary bytes prior to converting to
  unicode.

  :param str keyword: line to look up
  :param bytes content: content to look through

  :returns: **bytes** value on the given line, **None** if the line doesn't
    exist

  :raises: **ValueError** if the content isn't bytes
  """

  if not isinstance(content, bytes):
    raise ValueError("Content must be bytes, got a %s" % type(content))

  line_match = re.search(stem.util.str_tools._to_bytes("^(opt )?%s(?:[%s]+(.*))?$" % (keyword, WHITESPACE)), content, re.MULTILINE)

  if line_match:
    value = line_match.groups()[1]
    return b"" if value is None else value
  else:
    return None


def _read_until_keywords(keywords, descriptor_file, inclusive = False, ignore_first = False, skip = False, end_position = None, include_ending_keyword = False):
  """
  Reads from the descriptor file until we get to one of the given keywords or reach the
  end of the file.

  :param str,list keywords: keyword(s) we want to read until
  :param file descriptor_file: file with the descriptor content
  :param bool inclusive: includes the line with the keyword if True
  :param bool ignore_first: doesn't check if the first line read has one of the
    given keywords
  :param bool skip: skips buffering content, returning None
  :param int end_position: end if we reach this point in the file
  :param bool include_ending_keyword: provides the keyword we broke on if **True**

  :returns: **list** with the lines until we find one of the keywords, this is
    a two value tuple with the ending keyword if include_ending_keyword is
    **True**
  """

  content = None if skip else []
  ending_keyword = None

  if isinstance(keywords, (bytes, unicode)):
    keywords = (keywords,)

  if ignore_first:
    first_line = descriptor_file.readline()

    if content is not None and first_line is not None:
      content.append(first_line)

  while True:
    last_position = descriptor_file.tell()

    if end_position and last_position >= end_position:
      break

    line = descriptor_file.readline()

    if not line:
      break  # EOF

    line_match = KEYWORD_LINE.match(stem.util.str_tools._to_unicode(line))

    if not line_match:
      # no spaces or tabs in the line
      line_keyword = stem.util.str_tools._to_unicode(line.strip())
    else:
      line_keyword = line_match.groups()[0]

    if line_keyword in keywords:
      ending_keyword = line_keyword

      if not inclusive:
        descriptor_file.seek(last_position)
      elif content is not None:
        content.append(line)

      break
    elif content is not None:
      content.append(line)

  if include_ending_keyword:
    return (content, ending_keyword)
  else:
    return content


def _get_pseudo_pgp_block(remaining_contents):
  """
  Checks if given contents begins with a pseudo-Open-PGP-style block and, if
  so, pops it off and provides it back to the caller.

  :param list remaining_contents: lines to be checked for a public key block

  :returns: **str** with the armor wrapped contents or None if it doesn't exist

  :raises: **ValueError** if the contents starts with a key block but it's
    malformed (for instance, if it lacks an ending line)
  """

  if not remaining_contents:
    return None  # nothing left

  block_match = PGP_BLOCK_START.match(remaining_contents[0])

  if block_match:
    block_type = block_match.groups()[0]
    block_lines = []
    end_line = PGP_BLOCK_END % block_type

    while True:
      if not remaining_contents:
        raise ValueError("Unterminated pgp style block (looking for '%s'):\n%s" % (end_line, "\n".join(block_lines)))

      line = remaining_contents.pop(0)
      block_lines.append(line)

      if line == end_line:
        return "\n".join(block_lines)
  else:
    return None


def _get_descriptor_components(raw_contents, validate, extra_keywords = ()):
  """
  Initial breakup of the server descriptor contents to make parsing easier.

  A descriptor contains a series of 'keyword lines' which are simply a keyword
  followed by an optional value. Lines can also be followed by a signature
  block.

  To get a sub-listing with just certain keywords use extra_keywords. This can
  be useful if we care about their relative ordering with respect to each
  other. For instance, we care about the ordering of 'accept' and 'reject'
  entries because this influences the resulting exit policy, but for everything
  else in server descriptors the order does not matter.

  :param str raw_contents: descriptor content provided by the relay
  :param bool validate: checks the validity of the descriptor's content if
    True, skips these checks otherwise
  :param list extra_keywords: entity keywords to put into a separate listing
    with ordering intact

  :returns:
    **collections.OrderedDict** with the 'keyword => (value, pgp key) entries'
    mappings. If a extra_keywords was provided then this instead provides a two
    value tuple, the second being a list of those entries.
  """

  entries = OrderedDict()
  extra_entries = []  # entries with a keyword in extra_keywords
  remaining_lines = raw_contents.split("\n")

  while remaining_lines:
    line = remaining_lines.pop(0)

    # V2 network status documents explicitly can contain blank lines...
    #
    #   "Implementations MAY insert blank lines for clarity between sections;
    #   these blank lines are ignored."
    #
    # ... and server descriptors end with an extra newline. But other documents
    # don't say how blank lines should be handled so globally ignoring them.

    if not line:
      continue

    # Some lines have an 'opt ' for backward compatibility. They should be
    # ignored. This prefix is being removed in...
    # https://trac.torproject.org/projects/tor/ticket/5124

    if line.startswith("opt "):
      line = line[4:]

    line_match = KEYWORD_LINE.match(line)

    if not line_match:
      if not validate:
        continue

      raise ValueError("Line contains invalid characters: %s" % line)

    keyword, value = line_match.groups()

    if value is None:
      value = ''

    try:
      block_contents = _get_pseudo_pgp_block(remaining_lines)
    except ValueError as exc:
      if not validate:
        continue

      raise exc

    if keyword in extra_keywords:
      extra_entries.append("%s %s" % (keyword, value))
    else:
      entries.setdefault(keyword, []).append((value, block_contents))

  if extra_keywords:
    return entries, extra_entries
  else:
    return entries

# importing at the end to avoid circular dependencies on our Descriptor class

import stem.descriptor.server_descriptor
import stem.descriptor.extrainfo_descriptor
import stem.descriptor.networkstatus
import stem.descriptor.microdescriptor
import stem.descriptor.tordnsel
