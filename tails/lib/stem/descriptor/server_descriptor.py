# Copyright 2012-2013, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Parsing for Tor server descriptors, which contains the infrequently changing
information about a Tor relay (contact information, exit policy, public keys,
etc). This information is provided from a few sources...

* control port via 'GETINFO desc/\*' queries
* the 'cached-descriptors' file in tor's data directory
* tor metrics, at https://metrics.torproject.org/data.html
* directory authorities and mirrors via their DirPort

**Module Overview:**

::

  ServerDescriptor - Tor server descriptor.
    |- RelayDescriptor - Server descriptor for a relay.
    |
    |- BridgeDescriptor - Scrubbed server descriptor for a bridge.
    |  |- is_scrubbed - checks if our content has been properly scrubbed
    |  +- get_scrubbing_issues - description of issues with our scrubbing
    |
    |- digest - calculates the upper-case hex digest value for our content
    |- get_unrecognized_lines - lines with unrecognized content
    |- get_annotations - dictionary of content prior to the descriptor entry
    +- get_annotation_lines - lines that provided the annotations
"""

import base64
import codecs
import datetime
import hashlib
import re

import stem.descriptor.extrainfo_descriptor
import stem.exit_policy
import stem.prereq
import stem.util.connection
import stem.util.str_tools
import stem.util.tor_tools
import stem.version

from stem.util import log

from stem.descriptor import (
  PGP_BLOCK_END,
  Descriptor,
  _get_bytes_field,
  _get_descriptor_components,
  _read_until_keywords,
)

try:
  # added in python 3.2
  from functools import lru_cache
except ImportError:
  from stem.util.lru_cache import lru_cache

# relay descriptors must have exactly one of the following
REQUIRED_FIELDS = (
  "router",
  "bandwidth",
  "published",
  "onion-key",
  "signing-key",
  "router-signature",
)

# optional entries that can appear at most once
SINGLE_FIELDS = (
  "platform",
  "fingerprint",
  "hibernating",
  "uptime",
  "contact",
  "read-history",
  "write-history",
  "eventdns",
  "family",
  "caches-extra-info",
  "extra-info-digest",
  "hidden-service-dir",
  "protocols",
  "allow-single-hop-exits",
  "ntor-onion-key",
)

DEFAULT_IPV6_EXIT_POLICY = stem.exit_policy.MicroExitPolicy("reject 1-65535")
REJECT_ALL_POLICY = stem.exit_policy.ExitPolicy("reject *:*")


def _parse_file(descriptor_file, is_bridge = False, validate = True, **kwargs):
  """
  Iterates over the server descriptors in a file.

  :param file descriptor_file: file with descriptor content
  :param bool is_bridge: parses the file as being a bridge descriptor
  :param bool validate: checks the validity of the descriptor's content if
    **True**, skips these checks otherwise
  :param dict kwargs: additional arguments for the descriptor constructor

  :returns: iterator for ServerDescriptor instances in the file

  :raises:
    * **ValueError** if the contents is malformed and validate is True
    * **IOError** if the file can't be read
  """

  # Handler for relay descriptors
  #
  # Cached descriptors consist of annotations followed by the descriptor
  # itself. For instance...
  #
  #   @downloaded-at 2012-03-14 16:31:05
  #   @source "145.53.65.130"
  #   router caerSidi 71.35.143.157 9001 0 0
  #   platform Tor 0.2.1.30 on Linux x86_64
  #   <rest of the descriptor content>
  #   router-signature
  #   -----BEGIN SIGNATURE-----
  #   <signature for the above descriptor>
  #   -----END SIGNATURE-----
  #
  # Metrics descriptor files are the same, but lack any annotations. The
  # following simply does the following...
  #
  #   - parse as annotations until we get to "router"
  #   - parse as descriptor content until we get to "router-signature" followed
  #     by the end of the signature block
  #   - construct a descriptor and provide it back to the caller
  #
  # Any annotations after the last server descriptor is ignored (never provided
  # to the caller).

  while True:
    annotations = _read_until_keywords("router", descriptor_file)
    descriptor_content = _read_until_keywords("router-signature", descriptor_file)

    # we've reached the 'router-signature', now include the pgp style block
    block_end_prefix = PGP_BLOCK_END.split(' ', 1)[0]
    descriptor_content += _read_until_keywords(block_end_prefix, descriptor_file, True)

    if descriptor_content:
      # strip newlines from annotations
      annotations = map(bytes.strip, annotations)

      descriptor_text = bytes.join(b"", descriptor_content)

      if is_bridge:
        yield BridgeDescriptor(descriptor_text, validate, annotations, **kwargs)
      else:
        yield RelayDescriptor(descriptor_text, validate, annotations, **kwargs)
    else:
      if validate and annotations:
        orphaned_annotations = stem.util.str_tools._to_unicode(b'\n'.join(annotations))
        raise ValueError('Content conform to being a server descriptor:\n%s' % orphaned_annotations)

      break  # done parsing descriptors


class ServerDescriptor(Descriptor):
  """
  Common parent for server descriptors.

  :var str nickname: **\*** relay's nickname
  :var str fingerprint: identity key fingerprint
  :var datetime published: **\*** time in UTC when this descriptor was made

  :var str address: **\*** IPv4 address of the relay
  :var int or_port: **\*** port used for relaying
  :var int socks_port: **\*** port used as client (deprecated, always **None**)
  :var int dir_port: **\*** port used for descriptor mirroring

  :var bytes platform: line with operating system and tor version
  :var stem.version.Version tor_version: version of tor
  :var str operating_system: operating system
  :var int uptime: uptime when published in seconds
  :var bytes contact: contact information
  :var stem.exit_policy.ExitPolicy exit_policy: **\*** stated exit policy
  :var stem.exit_policy.MicroExitPolicy exit_policy_v6: **\*** exit policy for IPv6
  :var set family: **\*** nicknames or fingerprints of declared family

  :var int average_bandwidth: **\*** average rate it's willing to relay in bytes/s
  :var int burst_bandwidth: **\*** burst rate it's willing to relay in bytes/s
  :var int observed_bandwidth: **\*** estimated capacity based on usage in bytes/s

  :var list link_protocols: link protocols supported by the relay
  :var list circuit_protocols: circuit protocols supported by the relay
  :var bool hibernating: **\*** hibernating when published
  :var bool allow_single_hop_exits: **\*** flag if single hop exiting is allowed
  :var bool extra_info_cache: **\*** flag if a mirror for extra-info documents
  :var str extra_info_digest: upper-case hex encoded digest of our extra-info document
  :var bool eventdns: flag for evdns backend (deprecated, always unset)
  :var list or_addresses: **\*** alternative for our address/or_port
    attributes, each entry is a tuple of the form (address (**str**), port
    (**int**), is_ipv6 (**bool**))

  Deprecated, moved to extra-info descriptor...

  :var datetime read_history_end: end of the sampling interval
  :var int read_history_interval: seconds per interval
  :var list read_history_values: bytes read during each interval

  :var datetime write_history_end: end of the sampling interval
  :var int write_history_interval: seconds per interval
  :var list write_history_values: bytes written during each interval

  **\*** attribute is either required when we're parsed with validation or has
  a default value, others are left as **None** if undefined
  """

  def __init__(self, raw_contents, validate = True, annotations = None):
    """
    Server descriptor constructor, created from an individual relay's
    descriptor content (as provided by "GETINFO desc/*", cached descriptors,
    and metrics).

    By default this validates the descriptor's content as it's parsed. This
    validation can be disables to either improve performance or be accepting of
    malformed data.

    :param str raw_contents: descriptor content provided by the relay
    :param bool validate: checks the validity of the descriptor's content if
      **True**, skips these checks otherwise
    :param list annotations: lines that appeared prior to the descriptor

    :raises: **ValueError** if the contents is malformed and validate is True
    """

    super(ServerDescriptor, self).__init__(raw_contents)

    # Only a few things can be arbitrary bytes according to the dir-spec, so
    # parsing them separately.

    self.platform = _get_bytes_field("platform", raw_contents)
    self.contact = _get_bytes_field("contact", raw_contents)

    raw_contents = stem.util.str_tools._to_unicode(raw_contents)

    self.nickname = None
    self.fingerprint = None
    self.published = None

    self.address = None
    self.or_port = None
    self.socks_port = None
    self.dir_port = None

    self.tor_version = None
    self.operating_system = None
    self.uptime = None
    self.exit_policy = None
    self.exit_policy_v6 = DEFAULT_IPV6_EXIT_POLICY
    self.family = set()

    self.average_bandwidth = None
    self.burst_bandwidth = None
    self.observed_bandwidth = None

    self.link_protocols = None
    self.circuit_protocols = None
    self.hibernating = False
    self.allow_single_hop_exits = False
    self.extra_info_cache = False
    self.extra_info_digest = None
    self.hidden_service_dir = None
    self.eventdns = None
    self.or_addresses = []

    self.read_history_end = None
    self.read_history_interval = None
    self.read_history_values = None

    self.write_history_end = None
    self.write_history_interval = None
    self.write_history_values = None

    self._unrecognized_lines = []

    self._annotation_lines = annotations if annotations else []

    # A descriptor contains a series of 'keyword lines' which are simply a
    # keyword followed by an optional value. Lines can also be followed by a
    # signature block.
    #
    # We care about the ordering of 'accept' and 'reject' entries because this
    # influences the resulting exit policy, but for everything else the order
    # does not matter so breaking it into key / value pairs.

    entries, policy = _get_descriptor_components(raw_contents, validate, ("accept", "reject"))

    if policy == [u'reject *:*']:
      self.exit_policy = REJECT_ALL_POLICY
    else:
      self.exit_policy = stem.exit_policy.ExitPolicy(*policy)

    self._parse(entries, validate)

    if validate:
      self._check_constraints(entries)

  def digest(self):
    """
    Provides the hex encoded sha1 of our content. This value is part of the
    network status entry for this relay.

    :returns: **unicode** with the upper-case hex digest value for this server descriptor
    """

    raise NotImplementedError("Unsupported Operation: this should be implemented by the ServerDescriptor subclass")

  def get_unrecognized_lines(self):
    return list(self._unrecognized_lines)

  @lru_cache()
  def get_annotations(self):
    """
    Provides content that appeared prior to the descriptor. If this comes from
    the cached-descriptors file then this commonly contains content like...

    ::

      @downloaded-at 2012-03-18 21:18:29
      @source "173.254.216.66"

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
    :func:`~stem.descriptor.server_descriptor.ServerDescriptor.get_annotations`
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

      if keyword == "router":
        # "router" nickname address ORPort SocksPort DirPort
        router_comp = value.split()

        if len(router_comp) < 5:
          if not validate:
            continue

          raise ValueError("Router line must have five values: %s" % line)

        if validate:
          if not stem.util.tor_tools.is_valid_nickname(router_comp[0]):
            raise ValueError("Router line entry isn't a valid nickname: %s" % router_comp[0])
          elif not stem.util.connection.is_valid_ipv4_address(router_comp[1]):
            raise ValueError("Router line entry isn't a valid IPv4 address: %s" % router_comp[1])
          elif not stem.util.connection.is_valid_port(router_comp[2], allow_zero = True):
            raise ValueError("Router line's ORPort is invalid: %s" % router_comp[2])
          elif not stem.util.connection.is_valid_port(router_comp[3], allow_zero = True):
            raise ValueError("Router line's SocksPort is invalid: %s" % router_comp[3])
          elif not stem.util.connection.is_valid_port(router_comp[4], allow_zero = True):
            raise ValueError("Router line's DirPort is invalid: %s" % router_comp[4])
        elif not (router_comp[2].isdigit() and router_comp[3].isdigit() and router_comp[4].isdigit()):
          continue

        self.nickname = router_comp[0]
        self.address = router_comp[1]
        self.or_port = int(router_comp[2])
        self.socks_port = None if router_comp[3] == '0' else int(router_comp[3])
        self.dir_port = None if router_comp[4] == '0' else int(router_comp[4])
      elif keyword == "bandwidth":
        # "bandwidth" bandwidth-avg bandwidth-burst bandwidth-observed
        bandwidth_comp = value.split()

        if len(bandwidth_comp) < 3:
          if not validate:
            continue

          raise ValueError("Bandwidth line must have three values: %s" % line)
        elif not bandwidth_comp[0].isdigit():
          if not validate:
            continue

          raise ValueError("Bandwidth line's average rate isn't numeric: %s" % bandwidth_comp[0])
        elif not bandwidth_comp[1].isdigit():
          if not validate:
            continue

          raise ValueError("Bandwidth line's burst rate isn't numeric: %s" % bandwidth_comp[1])
        elif not bandwidth_comp[2].isdigit():
          if not validate:
            continue

          raise ValueError("Bandwidth line's observed rate isn't numeric: %s" % bandwidth_comp[2])

        self.average_bandwidth = int(bandwidth_comp[0])
        self.burst_bandwidth = int(bandwidth_comp[1])
        self.observed_bandwidth = int(bandwidth_comp[2])
      elif keyword == "platform":
        # "platform" string

        # The platform attribute was set earlier. This line can contain any
        # arbitrary data, but tor seems to report its version followed by the
        # os like the following...
        #
        #   platform Tor 0.2.2.35 (git-73ff13ab3cc9570d) on Linux x86_64
        #
        # There's no guarantee that we'll be able to pick these out the
        # version, but might as well try to save our caller the effort.

        platform_match = re.match("^Tor (\S*).* on (.*)$", value)

        if platform_match:
          version_str, self.operating_system = platform_match.groups()

          try:
            self.tor_version = stem.version._get_version(version_str)
          except ValueError:
            pass
      elif keyword == "published":
        # "published" YYYY-MM-DD HH:MM:SS

        try:
          self.published = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
          if validate:
            raise ValueError("Published line's time wasn't parsable: %s" % line)
      elif keyword == "fingerprint":
        # This is forty hex digits split into space separated groups of four.
        # Checking that we match this pattern.

        fingerprint = value.replace(" ", "")

        if validate:
          for grouping in value.split(" "):
            if len(grouping) != 4:
              raise ValueError("Fingerprint line should have groupings of four hex digits: %s" % value)

          if not stem.util.tor_tools.is_valid_fingerprint(fingerprint):
            raise ValueError("Tor relay fingerprints consist of forty hex digits: %s" % value)

        self.fingerprint = fingerprint
      elif keyword == "hibernating":
        # "hibernating" 0|1 (in practice only set if one)

        if validate and not value in ("0", "1"):
          raise ValueError("Hibernating line had an invalid value, must be zero or one: %s" % value)

        self.hibernating = value == "1"
      elif keyword == "allow-single-hop-exits":
        self.allow_single_hop_exits = True
      elif keyword == "caches-extra-info":
        self.extra_info_cache = True
      elif keyword == "extra-info-digest":
        # this is forty hex digits which just so happens to be the same a
        # fingerprint

        if validate and not stem.util.tor_tools.is_valid_fingerprint(value):
          raise ValueError("Extra-info digests should consist of forty hex digits: %s" % value)

        self.extra_info_digest = value
      elif keyword == "hidden-service-dir":
        if value:
          self.hidden_service_dir = value.split(" ")
        else:
          self.hidden_service_dir = ["2"]
      elif keyword == "uptime":
        # We need to be tolerant of negative uptimes to accommodate a past tor
        # bug...
        #
        # Changes in version 0.1.2.7-alpha - 2007-02-06
        #  - If our system clock jumps back in time, don't publish a negative
        #    uptime in the descriptor. Also, don't let the global rate limiting
        #    buckets go absurdly negative.
        #
        # After parsing all of the attributes we'll double check that negative
        # uptimes only occurred prior to this fix.

        try:
          self.uptime = int(value)
        except ValueError:
          if not validate:
            continue

          raise ValueError("Uptime line must have an integer value: %s" % value)
      elif keyword == "contact":
        pass  # parsed as a bytes field earlier
      elif keyword == "protocols":
        protocols_match = re.match("^Link (.*) Circuit (.*)$", value)

        if protocols_match:
          link_versions, circuit_versions = protocols_match.groups()
          self.link_protocols = link_versions.split(" ")
          self.circuit_protocols = circuit_versions.split(" ")
        elif validate:
          raise ValueError("Protocols line did not match the expected pattern: %s" % line)
      elif keyword == "family":
        self.family = set(value.split(" "))
      elif keyword == "eventdns":
        self.eventdns = value == "1"
      elif keyword == "ipv6-policy":
        self.exit_policy_v6 = stem.exit_policy.MicroExitPolicy(value)
      elif keyword == "or-address":
        or_address_entries = [value for (value, _) in values]

        for entry in or_address_entries:
          line = "%s %s" % (keyword, entry)

          if not ":" in entry:
            if not validate:
              continue
            else:
              raise ValueError("or-address line missing a colon: %s" % line)

          address, port = entry.rsplit(':', 1)
          is_ipv6 = address.startswith("[") and address.endswith("]")

          if is_ipv6:
            address = address[1:-1]  # remove brackets

          if not ((not is_ipv6 and stem.util.connection.is_valid_ipv4_address(address)) or
                 (is_ipv6 and stem.util.connection.is_valid_ipv6_address(address))):
            if not validate:
              continue
            else:
              raise ValueError("or-address line has a malformed address: %s" % line)

          if stem.util.connection.is_valid_port(port):
            self.or_addresses.append((address, int(port), is_ipv6))
          elif validate:
            raise ValueError("or-address line has a malformed port: %s" % line)
      elif keyword in ("read-history", "write-history"):
        try:
          timestamp, interval, remainder = \
            stem.descriptor.extrainfo_descriptor._parse_timestamp_and_interval(keyword, value)

          try:
            if remainder:
              history_values = [int(entry) for entry in remainder.split(",")]
            else:
              history_values = []
          except ValueError:
            raise ValueError("%s line has non-numeric values: %s" % (keyword, line))

          if keyword == "read-history":
            self.read_history_end = timestamp
            self.read_history_interval = interval
            self.read_history_values = history_values
          else:
            self.write_history_end = timestamp
            self.write_history_interval = interval
            self.write_history_values = history_values
        except ValueError as exc:
          if validate:
            raise exc
      else:
        self._unrecognized_lines.append(line)

    # if we have a negative uptime and a tor version that shouldn't exhibit
    # this bug then fail validation

    if validate and self.uptime and self.tor_version:
      if self.uptime < 0 and self.tor_version >= stem.version.Version("0.1.2.7"):
        raise ValueError("Descriptor for version '%s' had a negative uptime value: %i" % (self.tor_version, self.uptime))

  def _check_constraints(self, entries):
    """
    Does a basic check that the entries conform to this descriptor type's
    constraints.

    :param dict entries: keyword => (value, pgp key) entries

    :raises: **ValueError** if an issue arises in validation
    """

    for keyword in self._required_fields():
      if not keyword in entries:
        raise ValueError("Descriptor must have a '%s' entry" % keyword)

    for keyword in self._single_fields():
      if keyword in entries and len(entries[keyword]) > 1:
        raise ValueError("The '%s' entry can only appear once in a descriptor" % keyword)

    expected_first_keyword = self._first_keyword()
    if expected_first_keyword and expected_first_keyword != entries.keys()[0]:
      raise ValueError("Descriptor must start with a '%s' entry" % expected_first_keyword)

    expected_last_keyword = self._last_keyword()
    if expected_last_keyword and expected_last_keyword != entries.keys()[-1]:
      raise ValueError("Descriptor must end with a '%s' entry" % expected_last_keyword)

    if not self.exit_policy:
      raise ValueError("Descriptor must have at least one 'accept' or 'reject' entry")

  # Constraints that the descriptor must meet to be valid. These can be None if
  # not applicable.

  def _required_fields(self):
    return REQUIRED_FIELDS

  def _single_fields(self):
    return REQUIRED_FIELDS + SINGLE_FIELDS

  def _first_keyword(self):
    return "router"

  def _last_keyword(self):
    return "router-signature"


class RelayDescriptor(ServerDescriptor):
  """
  Server descriptor (`descriptor specification
  <https://gitweb.torproject.org/torspec.git/blob/HEAD:/dir-spec.txt>`_)

  :var str onion_key: **\*** key used to encrypt EXTEND cells
  :var str ntor_onion_key: base64 key used to encrypt EXTEND in the ntor protocol
  :var str signing_key: **\*** relay's long-term identity key
  :var str signature: **\*** signature for this descriptor

  **\*** attribute is required when we're parsed with validation
  """

  def __init__(self, raw_contents, validate = True, annotations = None):
    self.onion_key = None
    self.ntor_onion_key = None
    self.signing_key = None
    self.signature = None

    super(RelayDescriptor, self).__init__(raw_contents, validate, annotations)

    # validate the descriptor if required
    if validate:
      self._validate_content()

  @lru_cache()
  def digest(self):
    """
    Provides the digest of our descriptor's content.

    :returns: the digest string encoded in uppercase hex

    :raises: ValueError if the digest canot be calculated
    """

    # Digest is calculated from everything in the
    # descriptor except the router-signature.

    raw_descriptor = self.get_bytes()
    start_token = b"router "
    sig_token = b"\nrouter-signature\n"
    start = raw_descriptor.find(start_token)
    sig_start = raw_descriptor.find(sig_token)
    end = sig_start + len(sig_token)

    if start >= 0 and sig_start > 0 and end > start:
      for_digest = raw_descriptor[start:end]
      digest_hash = hashlib.sha1(stem.util.str_tools._to_bytes(for_digest))
      return stem.util.str_tools._to_unicode(digest_hash.hexdigest().upper())
    else:
      raise ValueError("unable to calculate digest for descriptor")

  def _validate_content(self):
    """
    Validates that the descriptor content matches the signature.

    :raises: ValueError if the signature does not match the content
    """

    key_as_bytes = RelayDescriptor._get_key_bytes(self.signing_key)

    # ensure the fingerprint is a hash of the signing key

    if self.fingerprint:
      # calculate the signing key hash

      key_der_as_hash = hashlib.sha1(stem.util.str_tools._to_bytes(key_as_bytes)).hexdigest()

      if key_der_as_hash != self.fingerprint.lower():
        log.warn("Signing key hash: %s != fingerprint: %s" % (key_der_as_hash, self.fingerprint.lower()))
        raise ValueError("Fingerprint does not match hash")

    self._verify_digest(key_as_bytes)

  def _verify_digest(self, key_as_der):
    # check that our digest matches what was signed

    if not stem.prereq.is_crypto_available():
      return

    from Crypto.Util import asn1
    from Crypto.Util.number import bytes_to_long, long_to_bytes

    # get the ASN.1 sequence

    seq = asn1.DerSequence()
    seq.decode(key_as_der)
    modulus = seq[0]
    public_exponent = seq[1]  # should always be 65537

    sig_as_bytes = RelayDescriptor._get_key_bytes(self.signature)

    # convert the descriptor signature to an int

    sig_as_long = bytes_to_long(sig_as_bytes)

    # use the public exponent[e] & the modulus[n] to decrypt the int

    decrypted_int = pow(sig_as_long, public_exponent, modulus)

    # block size will always be 128 for a 1024 bit key

    blocksize = 128

    # convert the int to a byte array.

    decrypted_bytes = long_to_bytes(decrypted_int, blocksize)

    ############################################################################
    ## The decrypted bytes should have a structure exactly along these lines.
    ## 1 byte  - [null '\x00']
    ## 1 byte  - [block type identifier '\x01'] - Should always be 1
    ## N bytes - [padding '\xFF' ]
    ## 1 byte  - [separator '\x00' ]
    ## M bytes - [message]
    ## Total   - 128 bytes
    ## More info here http://www.ietf.org/rfc/rfc2313.txt
    ##                esp the Notes in section 8.1
    ############################################################################

    try:
      if decrypted_bytes.index(b'\x00\x01') != 0:
        raise ValueError("Verification failed, identifier missing")
    except ValueError:
      raise ValueError("Verification failed, malformed data")

    try:
      identifier_offset = 2

      # find the separator
      seperator_index = decrypted_bytes.index(b'\x00', identifier_offset)
    except ValueError:
      raise ValueError("Verification failed, seperator not found")

    digest_hex = codecs.encode(decrypted_bytes[seperator_index + 1:], 'hex_codec')
    digest = stem.util.str_tools._to_unicode(digest_hex.upper())

    local_digest = self.digest()

    if digest != local_digest:
      raise ValueError("Decrypted digest does not match local digest (calculated: %s, local: %s)" % (digest, local_digest))

  def _parse(self, entries, validate):
    entries = dict(entries)  # shallow copy since we're destructive

    # handles fields only in server descriptors

    for keyword, values in entries.items():
      value, block_contents = values[0]
      line = "%s %s" % (keyword, value)

      if keyword == "onion-key":
        if validate and not block_contents:
          raise ValueError("Onion key line must be followed by a public key: %s" % line)

        self.onion_key = block_contents
        del entries["onion-key"]
      elif keyword == "ntor-onion-key":
        self.ntor_onion_key = value
        del entries["ntor-onion-key"]
      elif keyword == "signing-key":
        if validate and not block_contents:
          raise ValueError("Signing key line must be followed by a public key: %s" % line)

        self.signing_key = block_contents
        del entries["signing-key"]
      elif keyword == "router-signature":
        if validate and not block_contents:
          raise ValueError("Router signature line must be followed by a signature block: %s" % line)

        self.signature = block_contents
        del entries["router-signature"]

    ServerDescriptor._parse(self, entries, validate)

  def _compare(self, other, method):
    if not isinstance(other, RelayDescriptor):
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

  @staticmethod
  def _get_key_bytes(key_string):
    # Remove the newlines from the key string & strip off the
    # '-----BEGIN RSA PUBLIC KEY-----' header and
    # '-----END RSA PUBLIC KEY-----' footer

    key_as_string = ''.join(key_string.split('\n')[1:4])

    # get the key representation in bytes

    key_bytes = base64.b64decode(stem.util.str_tools._to_bytes(key_as_string))

    return key_bytes


class BridgeDescriptor(ServerDescriptor):
  """
  Bridge descriptor (`bridge descriptor specification
  <https://metrics.torproject.org/formats.html#bridgedesc>`_)
  """

  def __init__(self, raw_contents, validate = True, annotations = None):
    self._digest = None

    super(BridgeDescriptor, self).__init__(raw_contents, validate, annotations)

  def digest(self):
    return self._digest

  def _parse(self, entries, validate):
    entries = dict(entries)

    # handles fields only in bridge descriptors
    for keyword, values in entries.items():
      value, block_contents = values[0]
      line = "%s %s" % (keyword, value)

      if keyword == "router-digest":
        if validate and not stem.util.tor_tools.is_hex_digits(value, 40):
          raise ValueError("Router digest line had an invalid sha1 digest: %s" % line)

        self._digest = stem.util.str_tools._to_unicode(value)
        del entries["router-digest"]

    ServerDescriptor._parse(self, entries, validate)

  def is_scrubbed(self):
    """
    Checks if we've been properly scrubbed in accordance with the `bridge
    descriptor specification
    <https://metrics.torproject.org/formats.html#bridgedesc>`_. Validation is a
    moving target so this may not
    be fully up to date.

    :returns: **True** if we're scrubbed, **False** otherwise
    """

    return self.get_scrubbing_issues() == []

  @lru_cache()
  def get_scrubbing_issues(self):
    """
    Provides issues with our scrubbing.

    :returns: **list** of strings which describe issues we have with our
      scrubbing, this list is empty if we're properly scrubbed
    """

    issues = []

    if not self.address.startswith("10."):
      issues.append("Router line's address should be scrubbed to be '10.x.x.x': %s" % self.address)

    if self.contact and self.contact != "somebody":
      issues.append("Contact line should be scrubbed to be 'somebody', but instead had '%s'" % self.contact)

    for address, _, is_ipv6 in self.or_addresses:
      if not is_ipv6 and not address.startswith("10."):
        issues.append("or-address line's address should be scrubbed to be '10.x.x.x': %s" % address)
      elif is_ipv6 and not address.startswith("fd9f:2e19:3bcf::"):
        # TODO: this check isn't quite right because we aren't checking that
        # the next grouping of hex digits contains 1-2 digits
        issues.append("or-address line's address should be scrubbed to be 'fd9f:2e19:3bcf::xx:xxxx': %s" % address)

    for line in self.get_unrecognized_lines():
      if line.startswith("onion-key "):
        issues.append("Bridge descriptors should have their onion-key scrubbed: %s" % line)
      elif line.startswith("signing-key "):
        issues.append("Bridge descriptors should have their signing-key scrubbed: %s" % line)
      elif line.startswith("router-signature "):
        issues.append("Bridge descriptors should have their signature scrubbed: %s" % line)

    return issues

  def _required_fields(self):
    # bridge required fields are the same as a relay descriptor, minus items
    # excluded according to the format page

    excluded_fields = [
      "onion-key",
      "signing-key",
      "router-signature",
    ]

    included_fields = [
      "router-digest",
    ]

    return tuple(included_fields + [f for f in REQUIRED_FIELDS if not f in excluded_fields])

  def _single_fields(self):
    return self._required_fields() + SINGLE_FIELDS

  def _last_keyword(self):
    return None

  def _compare(self, other, method):
    if not isinstance(other, BridgeDescriptor):
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
