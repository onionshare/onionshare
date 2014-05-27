# Copyright 2012-2013, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Parsing for Tor extra-info descriptors. These are published by relays whenever
their server descriptor is published and have a similar format. However, unlike
server descriptors these don't contain information that Tor clients require to
function and as such aren't fetched by default.

Defined in section 2.2 of the `dir-spec
<https://gitweb.torproject.org/torspec.git/blob/HEAD:/dir-spec.txt>`_,
extra-info descriptors contain interesting but non-vital information such as
usage statistics. Tor clients cannot request these documents for bridges.

Extra-info descriptors are available from a few sources...

* if you have 'DownloadExtraInfo 1' in your torrc...

 * control port via 'GETINFO extra-info/digest/\*' queries
 * the 'cached-extrainfo' file in tor's data directory

* tor metrics, at https://metrics.torproject.org/data.html
* directory authorities and mirrors via their DirPort

**Module Overview:**

::

  ExtraInfoDescriptor - Tor extra-info descriptor.
    |  |- RelayExtraInfoDescriptor - Extra-info descriptor for a relay.
    |  +- BridgeExtraInfoDescriptor - Extra-info descriptor for a bridge.
    |
    |- digest - calculates the upper-case hex digest value for our content
    +- get_unrecognized_lines - lines with unrecognized content

.. data:: DirResponse (enum)

  Enumeration for known statuses for ExtraInfoDescriptor's dir_*_responses.

  =================== ===========
  DirResponse         Description
  =================== ===========
  **OK**              network status requests that were answered
  **NOT_ENOUGH_SIGS** network status wasn't signed by enough authorities
  **UNAVAILABLE**     requested network status was unavailable
  **NOT_FOUND**       requested network status was not found
  **NOT_MODIFIED**    network status unmodified since If-Modified-Since time
  **BUSY**            directory was busy
  =================== ===========

.. data:: DirStat (enum)

  Enumeration for known stats for ExtraInfoDescriptor's dir_*_direct_dl and
  dir_*_tunneled_dl.

  ===================== ===========
  DirStat               Description
  ===================== ===========
  **COMPLETE**          requests that completed successfully
  **TIMEOUT**           requests that didn't complete within a ten minute timeout
  **RUNNING**           requests still in process when measurement's taken
  **MIN**               smallest rate at which a descriptor was downloaded in B/s
  **MAX**               largest rate at which a descriptor was downloaded in B/s
  **D1-4** and **D6-9** rate of the slowest x/10 download rates in B/s
  **Q1** and **Q3**     rate of the slowest and fastest quarter download rates in B/s
  **MD**                median download rate in B/s
  ===================== ===========
"""

import datetime
import hashlib
import re

import stem.util.connection
import stem.util.enum
import stem.util.str_tools

from stem.descriptor import (
  PGP_BLOCK_END,
  Descriptor,
  _read_until_keywords,
  _get_descriptor_components,
)

try:
  # added in python 3.2
  from functools import lru_cache
except ImportError:
  from stem.util.lru_cache import lru_cache

# known statuses for dirreq-v2-resp and dirreq-v3-resp...
DirResponse = stem.util.enum.Enum(
  ("OK", "ok"),
  ("NOT_ENOUGH_SIGS", "not-enough-sigs"),
  ("UNAVAILABLE", "unavailable"),
  ("NOT_FOUND", "not-found"),
  ("NOT_MODIFIED", "not-modified"),
  ("BUSY", "busy"),
)

# known stats for dirreq-v2/3-direct-dl and dirreq-v2/3-tunneled-dl...
dir_stats = ['complete', 'timeout', 'running', 'min', 'max', 'q1', 'q3', 'md']
dir_stats += ['d%i' % i for i in range(1, 5)]
dir_stats += ['d%i' % i for i in range(6, 10)]
DirStat = stem.util.enum.Enum(*[(stat.upper(), stat) for stat in dir_stats])

# relay descriptors must have exactly one of the following
REQUIRED_FIELDS = (
  "extra-info",
  "published",
  "router-signature",
)

# optional entries that can appear at most once
SINGLE_FIELDS = (
  "read-history",
  "write-history",
  "geoip-db-digest",
  "geoip6-db-digest",
  "bridge-stats-end",
  "bridge-ips",
  "dirreq-stats-end",
  "dirreq-v2-ips",
  "dirreq-v3-ips",
  "dirreq-v2-reqs",
  "dirreq-v3-reqs",
  "dirreq-v2-share",
  "dirreq-v3-share",
  "dirreq-v2-resp",
  "dirreq-v3-resp",
  "dirreq-v2-direct-dl",
  "dirreq-v3-direct-dl",
  "dirreq-v2-tunneled-dl",
  "dirreq-v3-tunneled-dl",
  "dirreq-read-history",
  "dirreq-write-history",
  "entry-stats-end",
  "entry-ips",
  "cell-stats-end",
  "cell-processed-cells",
  "cell-queued-cells",
  "cell-time-in-queue",
  "cell-circuits-per-decile",
  "conn-bi-direct",
  "exit-stats-end",
  "exit-kibibytes-written",
  "exit-kibibytes-read",
  "exit-streams-opened",
)


def _parse_file(descriptor_file, is_bridge = False, validate = True, **kwargs):
  """
  Iterates over the extra-info descriptors in a file.

  :param file descriptor_file: file with descriptor content
  :param bool is_bridge: parses the file as being a bridge descriptor
  :param bool validate: checks the validity of the descriptor's content if
    **True**, skips these checks otherwise
  :param dict kwargs: additional arguments for the descriptor constructor

  :returns: iterator for :class:`~stem.descriptor.extrainfo_descriptor.ExtraInfoDescriptor`
    instances in the file

  :raises:
    * **ValueError** if the contents is malformed and validate is **True**
    * **IOError** if the file can't be read
  """

  while True:
    extrainfo_content = _read_until_keywords("router-signature", descriptor_file)

    # we've reached the 'router-signature', now include the pgp style block
    block_end_prefix = PGP_BLOCK_END.split(' ', 1)[0]
    extrainfo_content += _read_until_keywords(block_end_prefix, descriptor_file, True)

    if extrainfo_content:
      if is_bridge:
        yield BridgeExtraInfoDescriptor(bytes.join(b"", extrainfo_content), validate, **kwargs)
      else:
        yield RelayExtraInfoDescriptor(bytes.join(b"", extrainfo_content), validate, **kwargs)
    else:
      break  # done parsing file


def _parse_timestamp_and_interval(keyword, content):
  """
  Parses a 'YYYY-MM-DD HH:MM:SS (NSEC s) *' entry.

  :param str keyword: line's keyword
  :param str content: line content to be parsed

  :returns: **tuple** of the form (timestamp (**datetime**), interval
    (**int**), remaining content (**str**))

  :raises: **ValueError** if the content is malformed
  """

  line = "%s %s" % (keyword, content)
  content_match = re.match("^(.*) \(([0-9]+) s\)( .*)?$", content)

  if not content_match:
    raise ValueError("Malformed %s line: %s" % (keyword, line))

  timestamp_str, interval, remainder = content_match.groups()

  if remainder:
    remainder = remainder[1:]  # remove leading space

  if not interval.isdigit():
    raise ValueError("%s line's interval wasn't a number: %s" % (keyword, line))

  try:
    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    return timestamp, int(interval), remainder
  except ValueError:
    raise ValueError("%s line's timestamp wasn't parsable: %s" % (keyword, line))


class ExtraInfoDescriptor(Descriptor):
  """
  Extra-info descriptor document.

  :var str nickname: **\*** relay's nickname
  :var str fingerprint: **\*** identity key fingerprint
  :var datetime published: **\*** time in UTC when this descriptor was made
  :var str geoip_db_digest: sha1 of the geoIP database file for IPv4 addresses
  :var str geoip6_db_digest: sha1 of the geoIP database file for IPv6 addresses
  :var dict transport: **\*** mapping of transport methods to their (address,
    port, args) tuple, these usually appear on bridges in which case all of
    those are **None**

  **Bi-directional connection usage:**

  :var datetime conn_bi_direct_end: end of the sampling interval
  :var int conn_bi_direct_interval: seconds per interval
  :var int conn_bi_direct_below: connections that read/wrote less than 20 KiB
  :var int conn_bi_direct_read: connections that read at least 10x more than wrote
  :var int conn_bi_direct_write: connections that wrote at least 10x more than read
  :var int conn_bi_direct_both: remaining connections

  **Bytes read/written for relayed traffic:**

  :var datetime read_history_end: end of the sampling interval
  :var int read_history_interval: seconds per interval
  :var list read_history_values: bytes read during each interval

  :var datetime write_history_end: end of the sampling interval
  :var int write_history_interval: seconds per interval
  :var list write_history_values: bytes written during each interval

  **Cell relaying statistics:**

  :var datetime cell_stats_end: end of the period when stats were gathered
  :var int cell_stats_interval: length in seconds of the interval
  :var list cell_processed_cells: measurement of processed cells per circuit
  :var list cell_queued_cells: measurement of queued cells per circuit
  :var list cell_time_in_queue: mean enqueued time in milliseconds for cells
  :var int cell_circuits_per_decile: mean number of circuits in a decile

  **Directory Mirror Attributes:**

  :var datetime dir_stats_end: end of the period when stats were gathered
  :var int dir_stats_interval: length in seconds of the interval
  :var dict dir_v2_ips: mapping of locales to rounded count of requester ips
  :var dict dir_v3_ips: mapping of locales to rounded count of requester ips
  :var float dir_v2_share: percent of total directory traffic it expects to serve
  :var float dir_v3_share: percent of total directory traffic it expects to serve
  :var dict dir_v2_requests: mapping of locales to rounded count of requests
  :var dict dir_v3_requests: mapping of locales to rounded count of requests

  :var dict dir_v2_responses: mapping of :data:`~stem.descriptor.extrainfo_descriptor.DirResponse` to their rounded count
  :var dict dir_v3_responses: mapping of :data:`~stem.descriptor.extrainfo_descriptor.DirResponse` to their rounded count
  :var dict dir_v2_responses_unknown: mapping of unrecognized statuses to their count
  :var dict dir_v3_responses_unknown: mapping of unrecognized statuses to their count

  :var dict dir_v2_direct_dl: mapping of :data:`~stem.descriptor.extrainfo_descriptor.DirStat` to measurement over DirPort
  :var dict dir_v3_direct_dl: mapping of :data:`~stem.descriptor.extrainfo_descriptor.DirStat` to measurement over DirPort
  :var dict dir_v2_direct_dl_unknown: mapping of unrecognized stats to their measurement
  :var dict dir_v3_direct_dl_unknown: mapping of unrecognized stats to their measurement

  :var dict dir_v2_tunneled_dl: mapping of :data:`~stem.descriptor.extrainfo_descriptor.DirStat` to measurement over ORPort
  :var dict dir_v3_tunneled_dl: mapping of :data:`~stem.descriptor.extrainfo_descriptor.DirStat` to measurement over ORPort
  :var dict dir_v2_tunneled_dl_unknown: mapping of unrecognized stats to their measurement
  :var dict dir_v3_tunneled_dl_unknown: mapping of unrecognized stats to their measurement

  **Bytes read/written for directory mirroring:**

  :var datetime dir_read_history_end: end of the sampling interval
  :var int dir_read_history_interval: seconds per interval
  :var list dir_read_history_values: bytes read during each interval

  :var datetime dir_write_history_end: end of the sampling interval
  :var int dir_write_history_interval: seconds per interval
  :var list dir_write_history_values: bytes read during each interval

  **Guard Attributes:**

  :var datetime entry_stats_end: end of the period when stats were gathered
  :var int entry_stats_interval: length in seconds of the interval
  :var dict entry_ips: mapping of locales to rounded count of unique user ips

  **Exit Attributes:**

  :var datetime exit_stats_end: end of the period when stats were gathered
  :var int exit_stats_interval: length in seconds of the interval
  :var dict exit_kibibytes_written: traffic per port (keys are ints or 'other')
  :var dict exit_kibibytes_read: traffic per port (keys are ints or 'other')
  :var dict exit_streams_opened: streams per port (keys are ints or 'other')

  **Bridge Attributes:**

  :var datetime bridge_stats_end: end of the period when stats were gathered
  :var int bridge_stats_interval: length in seconds of the interval
  :var dict bridge_ips: mapping of locales to rounded count of unique user ips
  :var datetime geoip_start_time: replaced by bridge_stats_end (deprecated)
  :var dict geoip_client_origins: replaced by bridge_ips (deprecated)
  :var dict ip_versions: mapping of ip protocols to a rounded count for the number of users
  :var dict ip_versions: mapping of ip transports to a count for the number of users

  **\*** attribute is either required when we're parsed with validation or has
  a default value, others are left as **None** if undefined
  """

  def __init__(self, raw_contents, validate = True):
    """
    Extra-info descriptor constructor. By default this validates the
    descriptor's content as it's parsed. This validation can be disabled to
    either improve performance or be accepting of malformed data.

    :param str raw_contents: extra-info content provided by the relay
    :param bool validate: checks the validity of the extra-info descriptor if
      **True**, skips these checks otherwise

    :raises: **ValueError** if the contents is malformed and validate is True
    """

    super(ExtraInfoDescriptor, self).__init__(raw_contents)
    raw_contents = stem.util.str_tools._to_unicode(raw_contents)

    self.nickname = None
    self.fingerprint = None
    self.published = None
    self.geoip_db_digest = None
    self.geoip6_db_digest = None
    self.transport = {}

    self.conn_bi_direct_end = None
    self.conn_bi_direct_interval = None
    self.conn_bi_direct_below = None
    self.conn_bi_direct_read = None
    self.conn_bi_direct_write = None
    self.conn_bi_direct_both = None

    self.read_history_end = None
    self.read_history_interval = None
    self.read_history_values = None

    self.write_history_end = None
    self.write_history_interval = None
    self.write_history_values = None

    self.cell_stats_end = None
    self.cell_stats_interval = None
    self.cell_processed_cells = None
    self.cell_queued_cells = None
    self.cell_time_in_queue = None
    self.cell_circuits_per_decile = None

    self.dir_stats_end = None
    self.dir_stats_interval = None
    self.dir_v2_ips = None
    self.dir_v3_ips = None
    self.dir_v2_share = None
    self.dir_v3_share = None
    self.dir_v2_requests = None
    self.dir_v3_requests = None
    self.dir_v2_responses = None
    self.dir_v3_responses = None
    self.dir_v2_responses_unknown = None
    self.dir_v3_responses_unknown = None
    self.dir_v2_direct_dl = None
    self.dir_v3_direct_dl = None
    self.dir_v2_direct_dl_unknown = None
    self.dir_v3_direct_dl_unknown = None
    self.dir_v2_tunneled_dl = None
    self.dir_v3_tunneled_dl = None
    self.dir_v2_tunneled_dl_unknown = None
    self.dir_v3_tunneled_dl_unknown = None

    self.dir_read_history_end = None
    self.dir_read_history_interval = None
    self.dir_read_history_values = None

    self.dir_write_history_end = None
    self.dir_write_history_interval = None
    self.dir_write_history_values = None

    self.entry_stats_end = None
    self.entry_stats_interval = None
    self.entry_ips = None

    self.exit_stats_end = None
    self.exit_stats_interval = None
    self.exit_kibibytes_written = None
    self.exit_kibibytes_read = None
    self.exit_streams_opened = None

    self.bridge_stats_end = None
    self.bridge_stats_interval = None
    self.bridge_ips = None
    self.geoip_start_time = None
    self.geoip_client_origins = None

    self.ip_versions = None
    self.ip_transports = None

    self._unrecognized_lines = []

    entries = _get_descriptor_components(raw_contents, validate)

    if validate:
      for keyword in self._required_fields():
        if not keyword in entries:
          raise ValueError("Extra-info descriptor must have a '%s' entry" % keyword)

      for keyword in self._required_fields() + SINGLE_FIELDS:
        if keyword in entries and len(entries[keyword]) > 1:
          raise ValueError("The '%s' entry can only appear once in an extra-info descriptor" % keyword)

      expected_first_keyword = self._first_keyword()
      if expected_first_keyword and expected_first_keyword != entries.keys()[0]:
        raise ValueError("Extra-info descriptor must start with a '%s' entry" % expected_first_keyword)

      expected_last_keyword = self._last_keyword()
      if expected_last_keyword and expected_last_keyword != entries.keys()[-1]:
        raise ValueError("Descriptor must end with a '%s' entry" % expected_last_keyword)

    self._parse(entries, validate)

  def get_unrecognized_lines(self):
    return list(self._unrecognized_lines)

  def _parse(self, entries, validate):
    """
    Parses a series of 'keyword => (value, pgp block)' mappings and applies
    them as attributes.

    :param dict entries: descriptor contents to be applied
    :param bool validate: checks the validity of descriptor content if True

    :raises: **ValueError** if an error occurs in validation
    """

    for keyword, values in entries.items():
      # most just work with the first (and only) value
      value, _ = values[0]
      line = "%s %s" % (keyword, value)  # original line

      if keyword == "extra-info":
        # "extra-info" Nickname Fingerprint
        extra_info_comp = value.split()

        if len(extra_info_comp) < 2:
          if not validate:
            continue

          raise ValueError("Extra-info line must have two values: %s" % line)

        if validate:
          if not stem.util.tor_tools.is_valid_nickname(extra_info_comp[0]):
            raise ValueError("Extra-info line entry isn't a valid nickname: %s" % extra_info_comp[0])
          elif not stem.util.tor_tools.is_valid_fingerprint(extra_info_comp[1]):
            raise ValueError("Tor relay fingerprints consist of forty hex digits: %s" % extra_info_comp[1])

        self.nickname = extra_info_comp[0]
        self.fingerprint = extra_info_comp[1]
      elif keyword == "geoip-db-digest":
        # "geoip-db-digest" Digest

        if validate and not stem.util.tor_tools.is_hex_digits(value, 40):
          raise ValueError("Geoip digest line had an invalid sha1 digest: %s" % line)

        self.geoip_db_digest = value
      elif keyword == "geoip6-db-digest":
        # "geoip6-db-digest" Digest

        if validate and not stem.util.tor_tools.is_hex_digits(value, 40):
          raise ValueError("Geoip v6 digest line had an invalid sha1 digest: %s" % line)

        self.geoip6_db_digest = value
      elif keyword == "transport":
        # "transport" transportname address:port [arglist]
        # Everything after the transportname is scrubbed in published bridge
        # descriptors, so we'll never see it in practice.
        #
        # These entries really only make sense for bridges, but have been seen
        # on non-bridges in the wild when the relay operator configured it this
        # way.

        for transport_value, _ in values:
          name, address, port, args = None, None, None, None

          if not ' ' in transport_value:
            # scrubbed
            name = transport_value
          else:
            # not scrubbed
            value_comp = transport_value.split()

            if len(value_comp) < 1:
              raise ValueError("Transport line is missing its transport name: %s" % line)
            else:
              name = value_comp[0]

            if len(value_comp) < 2:
              raise ValueError("Transport line is missing its address:port value: %s" % line)
            elif not ":" in value_comp[1]:
              raise ValueError("Transport line's address:port entry is missing a colon: %s" % line)
            else:
              address, port_str = value_comp[1].split(':', 1)

              if not stem.util.connection.is_valid_ipv4_address(address) or \
                     stem.util.connection.is_valid_ipv6_address(address):
                raise ValueError("Transport line has a malformed address: %s" % line)
              elif not stem.util.connection.is_valid_port(port_str):
                raise ValueError("Transport line has a malformed port: %s" % line)

              port = int(port_str)

            if len(value_comp) >= 3:
              args = value_comp[2:]
            else:
              args = []

          self.transport[name] = (address, port, args)
      elif keyword == "cell-circuits-per-decile":
        # "cell-circuits-per-decile" num

        if not value.isdigit():
          if validate:
            raise ValueError("Non-numeric cell-circuits-per-decile value: %s" % line)
          else:
            continue

        stat = int(value)

        if validate and stat < 0:
          raise ValueError("Negative cell-circuits-per-decile value: %s" % line)

        self.cell_circuits_per_decile = stat
      elif keyword in ("dirreq-v2-resp", "dirreq-v3-resp", "dirreq-v2-direct-dl", "dirreq-v3-direct-dl", "dirreq-v2-tunneled-dl", "dirreq-v3-tunneled-dl"):
        recognized_counts = {}
        unrecognized_counts = {}

        is_response_stats = keyword in ("dirreq-v2-resp", "dirreq-v3-resp")
        key_set = DirResponse if is_response_stats else DirStat

        key_type = "STATUS" if is_response_stats else "STAT"
        error_msg = "%s lines should contain %s=COUNT mappings: %s" % (keyword, key_type, line)

        if value:
          for entry in value.split(","):
            if not "=" in entry:
              if validate:
                raise ValueError(error_msg)
              else:
                continue

            status, count = entry.split("=", 1)

            if count.isdigit():
              if status in key_set:
                recognized_counts[status] = int(count)
              else:
                unrecognized_counts[status] = int(count)
            elif validate:
              raise ValueError(error_msg)

        if keyword == "dirreq-v2-resp":
          self.dir_v2_responses = recognized_counts
          self.dir_v2_responses_unknown = unrecognized_counts
        elif keyword == "dirreq-v3-resp":
          self.dir_v3_responses = recognized_counts
          self.dir_v3_responses_unknown = unrecognized_counts
        elif keyword == "dirreq-v2-direct-dl":
          self.dir_v2_direct_dl = recognized_counts
          self.dir_v2_direct_dl_unknown = unrecognized_counts
        elif keyword == "dirreq-v3-direct-dl":
          self.dir_v3_direct_dl = recognized_counts
          self.dir_v3_direct_dl_unknown = unrecognized_counts
        elif keyword == "dirreq-v2-tunneled-dl":
          self.dir_v2_tunneled_dl = recognized_counts
          self.dir_v2_tunneled_dl_unknown = unrecognized_counts
        elif keyword == "dirreq-v3-tunneled-dl":
          self.dir_v3_tunneled_dl = recognized_counts
          self.dir_v3_tunneled_dl_unknown = unrecognized_counts
      elif keyword in ("dirreq-v2-share", "dirreq-v3-share"):
        # "<keyword>" num%

        try:
          if not value.endswith("%"):
            raise ValueError()

          percentage = float(value[:-1]) / 100

          # Bug lets these be above 100%, however they're soon going away...
          # https://lists.torproject.org/pipermail/tor-dev/2012-June/003679.html

          if validate and percentage < 0:
            raise ValueError("Negative percentage value: %s" % line)

          if keyword == "dirreq-v2-share":
            self.dir_v2_share = percentage
          elif keyword == "dirreq-v3-share":
            self.dir_v3_share = percentage
        except ValueError as exc:
          if validate:
            raise ValueError("Value can't be parsed as a percentage: %s" % line)
      elif keyword in ("cell-processed-cells", "cell-queued-cells", "cell-time-in-queue"):
        # "<keyword>" num,...,num

        entries = []

        if value:
          for entry in value.split(","):
            try:
              # Values should be positive but as discussed in ticket #5849
              # there was a bug around this. It was fixed in tor 0.2.2.1.

              entries.append(float(entry))
            except ValueError:
              if validate:
                raise ValueError("Non-numeric entry in %s listing: %s" % (keyword, line))

        if keyword == "cell-processed-cells":
          self.cell_processed_cells = entries
        elif keyword == "cell-queued-cells":
          self.cell_queued_cells = entries
        elif keyword == "cell-time-in-queue":
          self.cell_time_in_queue = entries
      elif keyword in ("published", "geoip-start-time"):
        # "<keyword>" YYYY-MM-DD HH:MM:SS

        try:
          timestamp = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

          if keyword == "published":
            self.published = timestamp
          elif keyword == "geoip-start-time":
            self.geoip_start_time = timestamp
        except ValueError:
          if validate:
            raise ValueError("Timestamp on %s line wasn't parsable: %s" % (keyword, line))
      elif keyword in ("cell-stats-end", "entry-stats-end", "exit-stats-end", "bridge-stats-end", "dirreq-stats-end"):
        # "<keyword>" YYYY-MM-DD HH:MM:SS (NSEC s)

        try:
          timestamp, interval, _ = _parse_timestamp_and_interval(keyword, value)

          if keyword == "cell-stats-end":
            self.cell_stats_end = timestamp
            self.cell_stats_interval = interval
          elif keyword == "entry-stats-end":
            self.entry_stats_end = timestamp
            self.entry_stats_interval = interval
          elif keyword == "exit-stats-end":
            self.exit_stats_end = timestamp
            self.exit_stats_interval = interval
          elif keyword == "bridge-stats-end":
            self.bridge_stats_end = timestamp
            self.bridge_stats_interval = interval
          elif keyword == "dirreq-stats-end":
            self.dir_stats_end = timestamp
            self.dir_stats_interval = interval
        except ValueError as exc:
          if validate:
            raise exc
      elif keyword == "conn-bi-direct":
        # "conn-bi-direct" YYYY-MM-DD HH:MM:SS (NSEC s) BELOW,READ,WRITE,BOTH

        try:
          timestamp, interval, remainder = _parse_timestamp_and_interval(keyword, value)
          stats = remainder.split(",")

          if len(stats) != 4 or not \
            (stats[0].isdigit() and stats[1].isdigit() and stats[2].isdigit() and stats[3].isdigit()):
            raise ValueError("conn-bi-direct line should end with four numeric values: %s" % line)

          self.conn_bi_direct_end = timestamp
          self.conn_bi_direct_interval = interval
          self.conn_bi_direct_below = int(stats[0])
          self.conn_bi_direct_read = int(stats[1])
          self.conn_bi_direct_write = int(stats[2])
          self.conn_bi_direct_both = int(stats[3])
        except ValueError as exc:
          if validate:
            raise exc
      elif keyword in ("read-history", "write-history", "dirreq-read-history", "dirreq-write-history"):
        # "<keyword>" YYYY-MM-DD HH:MM:SS (NSEC s) NUM,NUM,NUM,NUM,NUM...
        try:
          timestamp, interval, remainder = _parse_timestamp_and_interval(keyword, value)
          history_values = []

          if remainder:
            try:
              history_values = [int(entry) for entry in remainder.split(",")]
            except ValueError:
              raise ValueError("%s line has non-numeric values: %s" % (keyword, line))

          if keyword == "read-history":
            self.read_history_end = timestamp
            self.read_history_interval = interval
            self.read_history_values = history_values
          elif keyword == "write-history":
            self.write_history_end = timestamp
            self.write_history_interval = interval
            self.write_history_values = history_values
          elif keyword == "dirreq-read-history":
            self.dir_read_history_end = timestamp
            self.dir_read_history_interval = interval
            self.dir_read_history_values = history_values
          elif keyword == "dirreq-write-history":
            self.dir_write_history_end = timestamp
            self.dir_write_history_interval = interval
            self.dir_write_history_values = history_values
        except ValueError as exc:
          if validate:
            raise exc
      elif keyword in ("exit-kibibytes-written", "exit-kibibytes-read", "exit-streams-opened"):
        # "<keyword>" port=N,port=N,...

        port_mappings = {}
        error_msg = "Entries in %s line should only be PORT=N entries: %s" % (keyword, line)

        if value:
          for entry in value.split(","):
            if not "=" in entry:
              if validate:
                raise ValueError(error_msg)
              else:
                continue

            port, stat = entry.split("=", 1)

            if (port == 'other' or stem.util.connection.is_valid_port(port)) and stat.isdigit():
              if port != 'other':
                port = int(port)
              port_mappings[port] = int(stat)
            elif validate:
              raise ValueError(error_msg)

        if keyword == "exit-kibibytes-written":
          self.exit_kibibytes_written = port_mappings
        elif keyword == "exit-kibibytes-read":
          self.exit_kibibytes_read = port_mappings
        elif keyword == "exit-streams-opened":
          self.exit_streams_opened = port_mappings
      elif keyword in ("dirreq-v2-ips", "dirreq-v3-ips", "dirreq-v2-reqs", "dirreq-v3-reqs", "geoip-client-origins", "entry-ips", "bridge-ips"):
        # "<keyword>" CC=N,CC=N,...
        #
        # The maxmind geoip (https://www.maxmind.com/app/iso3166) has numeric
        # locale codes for some special values, for instance...
        #   A1,"Anonymous Proxy"
        #   A2,"Satellite Provider"
        #   ??,"Unknown"

        locale_usage = {}
        error_msg = "Entries in %s line should only be CC=N entries: %s" % (keyword, line)

        if value:
          for entry in value.split(","):
            if not "=" in entry:
              if validate:
                raise ValueError(error_msg)
              else:
                continue

            locale, count = entry.split("=", 1)

            if re.match("^[a-zA-Z0-9\?]{2}$", locale) and count.isdigit():
              locale_usage[locale] = int(count)
            elif validate:
              raise ValueError(error_msg)

        if keyword == "dirreq-v2-ips":
          self.dir_v2_ips = locale_usage
        elif keyword == "dirreq-v3-ips":
          self.dir_v3_ips = locale_usage
        elif keyword == "dirreq-v2-reqs":
          self.dir_v2_requests = locale_usage
        elif keyword == "dirreq-v3-reqs":
          self.dir_v3_requests = locale_usage
        elif keyword == "geoip-client-origins":
          self.geoip_client_origins = locale_usage
        elif keyword == "entry-ips":
          self.entry_ips = locale_usage
        elif keyword == "bridge-ips":
          self.bridge_ips = locale_usage
      elif keyword == "bridge-ip-versions":
        self.ip_versions = {}

        if value:
          for entry in value.split(','):
            if not '=' in entry:
              raise stem.ProtocolError("The bridge-ip-versions should be a comma separated listing of '<protocol>=<count>' mappings: %s" % line)

            protocol, count = entry.split('=', 1)

            if not count.isdigit():
              raise stem.ProtocolError("IP protocol count was non-numeric (%s): %s" % (count, line))

            self.ip_versions[protocol] = int(count)
      elif keyword == "bridge-ip-transports":
        self.ip_transports = {}

        if value:
          for entry in value.split(','):
            if not '=' in entry:
              raise stem.ProtocolError("The bridge-ip-transports should be a comma separated listing of '<protocol>=<count>' mappings: %s" % line)

            protocol, count = entry.split('=', 1)

            if not count.isdigit():
              raise stem.ProtocolError("Transport count was non-numeric (%s): %s" % (count, line))

            self.ip_transports[protocol] = int(count)
      else:
        self._unrecognized_lines.append(line)

  def digest(self):
    """
    Provides the upper-case hex encoded sha1 of our content. This value is part
    of the server descriptor entry for this relay.

    :returns: **str** with the upper-case hex digest value for this server
      descriptor
    """

    raise NotImplementedError("Unsupported Operation: this should be implemented by the ExtraInfoDescriptor subclass")

  def _required_fields(self):
    return REQUIRED_FIELDS

  def _first_keyword(self):
    return "extra-info"

  def _last_keyword(self):
    return "router-signature"


class RelayExtraInfoDescriptor(ExtraInfoDescriptor):
  """
  Relay extra-info descriptor, constructed from data such as that provided by
  "GETINFO extra-info/digest/\*", cached descriptors, and metrics
  (`specification <https://gitweb.torproject.org/torspec.git/blob/HEAD:/dir-spec.txt>`_).

  :var str signature: **\*** signature for this extrainfo descriptor

  **\*** attribute is required when we're parsed with validation
  """

  def __init__(self, raw_contents, validate = True):
    self.signature = None

    super(RelayExtraInfoDescriptor, self).__init__(raw_contents, validate)

  @lru_cache()
  def digest(self):
    # our digest is calculated from everything except our signature
    raw_content, ending = str(self), "\nrouter-signature\n"
    raw_content = raw_content[:raw_content.find(ending) + len(ending)]
    return hashlib.sha1(stem.util.str_tools._to_bytes(raw_content)).hexdigest().upper()

  def _parse(self, entries, validate):
    entries = dict(entries)  # shallow copy since we're destructive

    # handles fields only in server descriptors
    for keyword, values in entries.items():
      value, block_contents = values[0]

      line = "%s %s" % (keyword, value)  # original line

      if block_contents:
        line += "\n%s" % block_contents

      if keyword == "router-signature":
        if validate and not block_contents:
          raise ValueError("Router signature line must be followed by a signature block: %s" % line)

        self.signature = block_contents
        del entries["router-signature"]

    ExtraInfoDescriptor._parse(self, entries, validate)


class BridgeExtraInfoDescriptor(ExtraInfoDescriptor):
  """
  Bridge extra-info descriptor (`bridge descriptor specification
  <https://metrics.torproject.org/formats.html#bridgedesc>`_)
  """

  def __init__(self, raw_contents, validate = True):
    self._digest = None

    super(BridgeExtraInfoDescriptor, self).__init__(raw_contents, validate)

  def digest(self):
    return self._digest

  def _parse(self, entries, validate):
    entries = dict(entries)  # shallow copy since we're destructive

    # handles fields only in server descriptors
    for keyword, values in entries.items():
      value, _ = values[0]
      line = "%s %s" % (keyword, value)  # original line

      if keyword == "router-digest":
        if validate and not stem.util.tor_tools.is_hex_digits(value, 40):
          raise ValueError("Router digest line had an invalid sha1 digest: %s" % line)

        self._digest = value
        del entries["router-digest"]

    ExtraInfoDescriptor._parse(self, entries, validate)

  def _required_fields(self):
    excluded_fields = [
      "router-signature",
    ]

    included_fields = [
      "router-digest",
    ]

    return tuple(included_fields + [f for f in REQUIRED_FIELDS if not f in excluded_fields])

  def _last_keyword(self):
    return None
