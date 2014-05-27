# Copyright 2011-2013, Damian Johnson and The Tor Project
# See LICENSE for licensing information

"""
Classes for interacting with the tor control socket.

Controllers are a wrapper around a :class:`~stem.socket.ControlSocket`,
retaining many of its methods (connect, close, is_alive, etc) in addition to
providing its own for interacting at a higher level.

**Module Overview:**

::

  Controller - General controller class intended for direct use
    | |- from_port - Provides a Controller based on a port connection.
    | +- from_socket_file - Provides a Controller based on a socket file connection.
    |
    |- authenticate - authenticates this controller with tor
    |
    |- get_info - issues a GETINFO query for a parameter
    |- get_version - provides our tor version
    |- get_exit_policy - provides our exit policy
    |- get_socks_listeners - provides where tor is listening for SOCKS connections
    |- get_protocolinfo - information about the controller interface
    |- get_user - provides the user tor is running as
    |- get_pid - provides the pid of our tor process
    |
    |- get_microdescriptor - querying the microdescriptor for a relay
    |- get_microdescriptors - provides all presently available microdescriptors
    |- get_server_descriptor - querying the server descriptor for a relay
    |- get_server_descriptors - provides all presently available server descriptors
    |- get_network_status - querying the router status entry for a relay
    |- get_network_statuses - provides all preently available router status entries
    |
    |- get_conf - gets the value of a configuration option
    |- get_conf_map - gets the values of multiple configuration options
    |- set_conf - sets the value of a configuration option
    |- reset_conf - reverts configuration options to their default values
    |- set_options - sets or resets the values of multiple configuration options
    |
    |- add_event_listener - attaches an event listener to be notified of tor events
    |- remove_event_listener - removes a listener so it isn't notified of further events
    |
    |- is_caching_enabled - true if the controller has enabled caching
    |- set_caching - enables or disables caching
    |- clear_cache - clears any cached results
    |
    |- load_conf - loads configuration information as if it was in the torrc
    |- save_conf - saves configuration information to the torrc
    |
    |- is_feature_enabled - checks if a given controller feature is enabled
    |- enable_feature - enables a controller feature that has been disabled by default
    |
    |- get_circuit - provides an active circuit
    |- get_circuits - provides a list of active circuits
    |- new_circuit - create new circuits
    |- extend_circuit - create new circuits and extend existing ones
    |- repurpose_circuit - change a circuit's purpose
    |- close_circuit - close a circuit
    |
    |- get_streams - provides a list of active streams
    |- attach_stream - attach a stream to a circuit
    |- close_stream - close a stream
    |
    |- signal - sends a signal to the tor client
    |- is_geoip_unavailable - true if we've discovered our geoip db to be unavailable
    +- map_address - maps one address to another such that connections to the original are replaced with the other

  BaseController - Base controller class asynchronous message handling
    |- msg - communicates with the tor process
    |- is_alive - reports if our connection to tor is open or closed
    |- is_authenticated - checks if we're authenticated to tor
    |- connect - connects or reconnects to tor
    |- close - shuts down our connection to the tor process
    |- get_socket - provides the socket used for control communication
    |- get_latest_heartbeat - timestamp for when we last heard from tor
    |- add_status_listener - notifies a callback of changes in our status
    |- remove_status_listener - prevents further notification of status changes
    +- __enter__ / __exit__ - manages socket connection

.. data:: State (enum)

  Enumeration for states that a controller can have.

  ========== ===========
  State      Description
  ========== ===========
  **INIT**   new control connection
  **RESET**  received a reset/sighup signal
  **CLOSED** control connection closed
  ========== ===========

.. data:: EventType (enum)

  Known types of events that the
  :func:`~stem.control.Controller.add_event_listener` method of the
  :class:`~stem.control.Controller` can listen for.

  The most frequently listened for event types tend to be the logging events
  (**DEBUG**, **INFO**, **NOTICE**, **WARN**, and **ERR**), bandwidth usage
  (**BW**), and circuit or stream changes (**CIRC** and **STREAM**).

  Enums are mapped to :class:`~stem.response.events.Event` subclasses as
  follows...

  ===================== ===========
  EventType             Event Class
  ===================== ===========
  **ADDRMAP**           :class:`stem.response.events.AddrMapEvent`
  **AUTHDIR_NEWDESCS**  :class:`stem.response.events.AuthDirNewDescEvent`
  **BUILDTIMEOUT_SET**  :class:`stem.response.events.BuildTimeoutSetEvent`
  **BW**                :class:`stem.response.events.BandwidthEvent`
  **CIRC**              :class:`stem.response.events.CircuitEvent`
  **CIRC_MINOR**        :class:`stem.response.events.CircMinorEvent`
  **CLIENTS_SEEN**      :class:`stem.response.events.ClientsSeenEvent`
  **CONF_CHANGED**      :class:`stem.response.events.ConfChangedEvent`
  **DEBUG**             :class:`stem.response.events.LogEvent`
  **DESCCHANGED**       :class:`stem.response.events.DescChangedEvent`
  **ERR**               :class:`stem.response.events.LogEvent`
  **GUARD**             :class:`stem.response.events.GuardEvent`
  **INFO**              :class:`stem.response.events.LogEvent`
  **NEWCONSENSUS**      :class:`stem.response.events.NewConsensusEvent`
  **NEWDESC**           :class:`stem.response.events.NewDescEvent`
  **NOTICE**            :class:`stem.response.events.LogEvent`
  **NS**                :class:`stem.response.events.NetworkStatusEvent`
  **ORCONN**            :class:`stem.response.events.ORConnEvent`
  **SIGNAL**            :class:`stem.response.events.SignalEvent`
  **STATUS_CLIENT**     :class:`stem.response.events.StatusEvent`
  **STATUS_GENERAL**    :class:`stem.response.events.StatusEvent`
  **STATUS_SERVER**     :class:`stem.response.events.StatusEvent`
  **STREAM**            :class:`stem.response.events.StreamEvent`
  **STREAM_BW**         :class:`stem.response.events.StreamBwEvent`
  **WARN**              :class:`stem.response.events.LogEvent`
  ===================== ===========
"""

import io
import os
import Queue
import StringIO
import threading
import time

import stem.descriptor.microdescriptor
import stem.descriptor.reader
import stem.descriptor.router_status_entry
import stem.descriptor.server_descriptor
import stem.exit_policy
import stem.response
import stem.response.events
import stem.socket
import stem.util.connection
import stem.util.enum
import stem.util.str_tools
import stem.util.system
import stem.util.tor_tools
import stem.version

from stem import UNDEFINED, CircStatus, Signal
from stem.util import log

# state changes a control socket can have

State = stem.util.enum.Enum("INIT", "RESET", "CLOSED")

EventType = stem.util.enum.UppercaseEnum(
  "CIRC",
  "STREAM",
  "ORCONN",
  "BW",
  "DEBUG",
  "INFO",
  "NOTICE",
  "WARN",
  "ERR",
  "NEWDESC",
  "ADDRMAP",
  "AUTHDIR_NEWDESCS",
  "DESCCHANGED",
  "STATUS_GENERAL",
  "STATUS_CLIENT",
  "STATUS_SERVER",
  "GUARD",
  "NS",
  "STREAM_BW",
  "CLIENTS_SEEN",
  "NEWCONSENSUS",
  "BUILDTIMEOUT_SET",
  "SIGNAL",
  "CONF_CHANGED",
  "CIRC_MINOR",
)

# Configuration options that are fetched by a special key. The keys are
# lowercase to make case insensitive lookups easier.

MAPPED_CONFIG_KEYS = {
  "hiddenservicedir": "HiddenServiceOptions",
  "hiddenserviceport": "HiddenServiceOptions",
  "hiddenserviceversion": "HiddenServiceOptions",
  "hiddenserviceauthorizeclient": "HiddenServiceOptions",
  "hiddenserviceoptions": "HiddenServiceOptions"
}

# unchangeable GETINFO parameters

CACHEABLE_GETINFO_PARAMS = (
  'version',
  'config-file',
  'exit-policy/default',
  'fingerprint',
  'config/names',
  'config/defaults',
  'info/names',
  'events/names',
  'features/names',
  'process/descriptor-limit',
)

# GETCONF parameters we shouldn't cache. This includes hidden service
# perameters due to the funky way they're set and retrieved (for instance,
# 'SETCONF HiddenServiceDir' effects 'GETCONF HiddenServiceOptions').

UNCACHEABLE_GETCONF_PARAMS = (
  'hiddenserviceoptions',
  'hiddenservicedir',
  'hiddenserviceport',
  'hiddenserviceversion',
  'hiddenserviceauthorizeclient',
  'hiddenserviceoptions',
)

# number of sequential attempts before we decide that the Tor geoip database
# is unavailable
GEOIP_FAILURE_THRESHOLD = 5

SERVER_DESCRIPTORS_UNSUPPORTED = "Tor is presently not configured to retrieve \
server descriptors. As of Tor version 0.2.3.25 it downloads microdescriptors \
instead unless you set 'UseMicrodescriptors 0' in your torrc."


class BaseController(object):
  """
  Controller for the tor process. This is a minimal base class for other
  controllers, providing basic process communication and event listing. Don't
  use this directly - subclasses like the :class:`~stem.control.Controller`
  provide higher level functionality.

  It's highly suggested that you don't interact directly with the
  :class:`~stem.socket.ControlSocket` that we're constructed from - use our
  wrapper methods instead.
  """

  def __init__(self, control_socket):
    self._socket = control_socket
    self._msg_lock = threading.RLock()

    self._status_listeners = []  # tuples of the form (callback, spawn_thread)
    self._status_listeners_lock = threading.RLock()

    # queues where incoming messages are directed
    self._reply_queue = Queue.Queue()
    self._event_queue = Queue.Queue()

    # thread to continually pull from the control socket
    self._reader_thread = None

    # thread to pull from the _event_queue and call handle_event
    self._event_notice = threading.Event()
    self._event_thread = None

    # saves our socket's prior _connect() and _close() methods so they can be
    # called along with ours

    self._socket_connect = self._socket._connect
    self._socket_close = self._socket._close

    self._socket._connect = self._connect
    self._socket._close = self._close

    self._last_heartbeat = 0.0  # timestamp for when we last heard from tor
    self._is_authenticated = False

    if self._socket.is_alive():
      self._launch_threads()

  def msg(self, message):
    """
    Sends a message to our control socket and provides back its reply.

    :param str message: message to be formatted and sent to tor

    :returns: :class:`~stem.response.ControlMessage` with the response

    :raises:
      * :class:`stem.ProtocolError` the content from the socket is
        malformed
      * :class:`stem.SocketError` if a problem arises in using the
        socket
      * :class:`stem.SocketClosed` if the socket is shut down
    """

    with self._msg_lock:
      # If our _reply_queue isn't empty then one of a few things happened...
      #
      # - Our connection was closed and probably re-restablished. This was
      #   in reply to pulling for an asynchronous event and getting this is
      #   expected - ignore it.
      #
      # - Pulling for asynchronous events produced an error. If this was a
      #   ProtocolError then it's a tor bug, and if a non-closure SocketError
      #   then it was probably a socket glitch. Deserves an INFO level log
      #   message.
      #
      # - This is a leftover response for a msg() call. We can't tell who an
      #   exception was earmarked for, so we only know that this was the case
      #   if it's a ControlMessage. This should not be possible and indicates
      #   a stem bug. This deserves a NOTICE level log message since it
      #   indicates that one of our callers didn't get their reply.

      while not self._reply_queue.empty():
        try:
          response = self._reply_queue.get_nowait()

          if isinstance(response, stem.SocketClosed):
            pass  # this is fine
          elif isinstance(response, stem.ProtocolError):
            log.info("Tor provided a malformed message (%s)" % response)
          elif isinstance(response, stem.ControllerError):
            log.info("Socket experienced a problem (%s)" % response)
          elif isinstance(response, stem.response.ControlMessage):
            log.notice("BUG: the msg() function failed to deliver a response: %s" % response)
        except Queue.Empty:
          # the empty() method is documented to not be fully reliable so this
          # isn't entirely surprising

          break

      try:
        self._socket.send(message)
        response = self._reply_queue.get()

        # If the message we received back had an exception then re-raise it to the
        # caller. Otherwise return the response.

        if isinstance(response, stem.ControllerError):
          raise response
        else:
          # I really, really don't like putting hooks into this method, but
          # this is the most reliable method I can think of for taking actions
          # immediately after successfully authenticating to a connection.

          if message.upper().startswith("AUTHENTICATE"):
            self._post_authentication()

          return response
      except stem.SocketClosed as exc:
        # If the recv() thread caused the SocketClosed then we could still be
        # in the process of closing. Calling close() here so that we can
        # provide an assurance to the caller that when we raise a SocketClosed
        # exception we are shut down afterward for realz.

        self.close()
        raise exc

  def is_alive(self):
    """
    Checks if our socket is currently connected. This is a pass-through for our
    socket's :func:`~stem.socket.ControlSocket.is_alive` method.

    :returns: **bool** that's **True** if our socket is connected and **False** otherwise
    """

    return self._socket.is_alive()

  def is_authenticated(self):
    """
    Checks if our socket is both connected and authenticated.

    :returns: **bool** that's **True** if our socket is authenticated to tor
      and **False** otherwise
    """

    if self.is_alive():
      return self._is_authenticated

    return False

  def connect(self):
    """
    Reconnects our control socket. This is a pass-through for our socket's
    :func:`~stem.socket.ControlSocket.connect` method.

    :raises: :class:`stem.SocketError` if unable to make a socket
    """

    self._socket.connect()

  def close(self):
    """
    Closes our socket connection. This is a pass-through for our socket's
    :func:`~stem.socket.ControlSocket.close` method.
    """

    self._socket.close()

  def get_socket(self):
    """
    Provides the socket used to speak with the tor process. Communicating with
    the socket directly isn't advised since it may confuse this controller.

    :returns: :class:`~stem.socket.ControlSocket` we're communicating with
    """

    return self._socket

  def get_latest_heartbeat(self):
    """
    Provides the unix timestamp for when we last heard from tor. This is zero
    if we've never received a message.

    :returns: float for the unix timestamp of when we last heard from tor
    """

    return self._last_heartbeat

  def add_status_listener(self, callback, spawn = True):
    """
    Notifies a given function when the state of our socket changes. Functions
    are expected to be of the form...

    ::

      my_function(controller, state, timestamp)

    The state is a value from the :data:`stem.control.State` enum. Functions
    **must** allow for new values. The timestamp is a float for the unix time
    when the change occurred.

    This class only provides **State.INIT** and **State.CLOSED** notifications.
    Subclasses may provide others.

    If spawn is **True** then the callback is notified via a new daemon thread.
    If **False** then the notice is under our locks, within the thread where
    the change occurred. In general this isn't advised, especially if your
    callback could block for a while.

    :param function callback: function to be notified when our state changes
    :param bool spawn: calls function via a new thread if **True**, otherwise
      it's part of the connect/close method call
    """

    with self._status_listeners_lock:
      self._status_listeners.append((callback, spawn))

  def remove_status_listener(self, callback):
    """
    Stops listener from being notified of further events.

    :param function callback: function to be removed from our listeners

    :returns: **bool** that's **True** if we removed one or more occurrences of
      the callback, **False** otherwise
    """

    with self._status_listeners_lock:
      new_listeners, is_changed = [], False

      for listener, spawn in self._status_listeners:
        if listener != callback:
          new_listeners.append((listener, spawn))
        else:
          is_changed = True

      self._status_listeners = new_listeners
      return is_changed

  def __enter__(self):
    return self

  def __exit__(self, exit_type, value, traceback):
    self.close()

  def _handle_event(self, event_message):
    """
    Callback to be overwritten by subclasses for event listening. This is
    notified whenever we receive an event from the control socket.

    :param stem.response.ControlMessage event_message: message received from
      the control socket
    """

    pass

  def _connect(self):
    self._launch_threads()
    self._notify_status_listeners(State.INIT)
    self._socket_connect()
    self._is_authenticated = False

  def _close(self):
    # Our is_alive() state is now false. Our reader thread should already be
    # awake from recv() raising a closure exception. Wake up the event thread
    # too so it can end.

    self._event_notice.set()
    self._is_authenticated = False

    # joins on our threads if it's safe to do so

    for t in (self._reader_thread, self._event_thread):
      if t and t.is_alive() and threading.current_thread() != t:
        t.join()

    self._notify_status_listeners(State.CLOSED)
    self._socket_close()

  def _post_authentication(self):
    # actions to be taken after we have a newly authenticated connection

    self._is_authenticated = True

  def _notify_status_listeners(self, state):
    """
    Informs our status listeners that a state change occurred.

    :param stem.control.State state: state change that has occurred
    """

    # Any changes to our is_alive() state happen under the send lock, so we
    # need to have it to ensure it doesn't change beneath us.

    with self._socket._get_send_lock():
      with self._status_listeners_lock:
        # States imply that our socket is either alive or not, which may not
        # hold true when multiple events occur in quick succession. For
        # instance, a sighup could cause two events (State.RESET for the sighup
        # and State.CLOSE if it causes tor to crash). However, there's no
        # guarantee of the order in which they occur, and it would be bad if
        # listeners got the State.RESET last, implying that we were alive.

        expect_alive = None

        if state in (State.INIT, State.RESET):
          expect_alive = True
        elif state == State.CLOSED:
          expect_alive = False

        change_timestamp = time.time()

        if expect_alive is not None and expect_alive != self.is_alive():
          return

        for listener, spawn in self._status_listeners:
          if spawn:
            name = "%s notification" % state
            args = (self, state, change_timestamp)

            notice_thread = threading.Thread(target = listener, args = args, name = name)
            notice_thread.setDaemon(True)
            notice_thread.start()
          else:
            listener(self, state, change_timestamp)

  def _launch_threads(self):
    """
    Initializes daemon threads. Threads can't be reused so we need to recreate
    them if we're restarted.
    """

    # In theory concurrent calls could result in multiple start() calls on a
    # single thread, which would cause an unexpected exception. Best be safe.

    with self._socket._get_send_lock():
      if not self._reader_thread or not self._reader_thread.is_alive():
        self._reader_thread = threading.Thread(target = self._reader_loop, name = "Tor Listener")
        self._reader_thread.setDaemon(True)
        self._reader_thread.start()

      if not self._event_thread or not self._event_thread.is_alive():
        self._event_thread = threading.Thread(target = self._event_loop, name = "Event Notifier")
        self._event_thread.setDaemon(True)
        self._event_thread.start()

  def _reader_loop(self):
    """
    Continually pulls from the control socket, directing the messages into
    queues based on their type. Controller messages come in two varieties...

    * Responses to messages we've sent (GETINFO, SETCONF, etc).
    * Asynchronous events, identified by a status code of 650.
    """

    while self.is_alive():
      try:
        control_message = self._socket.recv()
        self._last_heartbeat = time.time()

        if control_message.content()[-1][0] == "650":
          # asynchronous message, adds to the event queue and wakes up its handler
          self._event_queue.put(control_message)
          self._event_notice.set()
        else:
          # response to a msg() call
          self._reply_queue.put(control_message)
      except stem.ControllerError as exc:
        # Assume that all exceptions belong to the reader. This isn't always
        # true, but the msg() call can do a better job of sorting it out.
        #
        # Be aware that the msg() method relies on this to unblock callers.

        self._reply_queue.put(exc)

  def _event_loop(self):
    """
    Continually pulls messages from the _event_queue and sends them to our
    handle_event callback. This is done via its own thread so subclasses with a
    lengthy handle_event implementation don't block further reading from the
    socket.
    """

    while True:
      try:
        event_message = self._event_queue.get_nowait()
        self._handle_event(event_message)
      except Queue.Empty:
        if not self.is_alive():
          break

        self._event_notice.wait()
        self._event_notice.clear()


class Controller(BaseController):
  """
  Communicates with a control socket. This is built on top of the
  BaseController and provides a more user friendly API for library users.
  """

  @staticmethod
  def from_port(address = "127.0.0.1", port = 9051):
    """
    Constructs a :class:`~stem.socket.ControlPort` based Controller.

    :param str address: ip address of the controller
    :param int port: port number of the controller

    :returns: :class:`~stem.control.Controller` attached to the given port

    :raises: :class:`stem.SocketError` if we're unable to establish a connection
    """

    if not stem.util.connection.is_valid_ipv4_address(address):
      raise ValueError("Invalid IP address: %s" % address)
    elif not stem.util.connection.is_valid_port(port):
      raise ValueError("Invalid port: %s" % port)

    control_port = stem.socket.ControlPort(address, port)
    return Controller(control_port)

  @staticmethod
  def from_socket_file(path = "/var/run/tor/control"):
    """
    Constructs a :class:`~stem.socket.ControlSocketFile` based Controller.

    :param str path: path where the control socket is located

    :returns: :class:`~stem.control.Controller` attached to the given socket file

    :raises: :class:`stem.SocketError` if we're unable to establish a connection
    """

    control_socket = stem.socket.ControlSocketFile(path)
    return Controller(control_socket)

  def __init__(self, control_socket):
    super(Controller, self).__init__(control_socket)

    self._is_caching_enabled = True
    self._request_cache = {}

    self._cache_lock = threading.RLock()

    # mapping of event types to their listeners

    self._event_listeners = {}
    self._event_listeners_lock = threading.RLock()

    # number of sequential 'GETINFO ip-to-country/*' lookups that have failed
    self._geoip_failure_count = 0
    self._enabled_features = []

    def _sighup_listener(event):
      if event.signal == Signal.RELOAD:
        self.clear_cache()
        self._notify_status_listeners(State.RESET)

    self.add_event_listener(_sighup_listener, EventType.SIGNAL)

    def _confchanged_listener(event):
      if self.is_caching_enabled():
        self._set_cache(dict((k, None) for k in event.config), "getconf")

        if "exitpolicy" in event.config.keys():
          self._set_cache({"exitpolicy": None})

    self.add_event_listener(_confchanged_listener, EventType.CONF_CHANGED)

  def connect(self):
    super(Controller, self).connect()
    self.clear_cache()

  def close(self):
    # making a best-effort attempt to quit before detaching the socket
    if self.is_alive():
      try:
        self.msg("QUIT")
      except:
        pass

      self.clear_cache()

    super(Controller, self).close()

  def authenticate(self, *args, **kwargs):
    """
    A convenience method to authenticate the controller. This is just a
    pass-through to :func:`stem.connection.authenticate`.
    """

    import stem.connection
    stem.connection.authenticate(self, *args, **kwargs)

  def get_info(self, params, default = UNDEFINED, get_bytes = False):
    """
    Queries the control socket for the given GETINFO option. If provided a
    default then that's returned if the GETINFO option is undefined or the
    call fails for any reason (error response, control port closed, initiated,
    etc).

    :param str,list params: GETINFO option or options to be queried
    :param object default: response if the query fails
    :param bool get_bytes: provides **bytes** values rather than a **str** under python 3.x

    :returns:
      Response depends upon how we were called as follows...

      * **str** with the response if our param was a **str**
      * **dict** with the 'param => response' mapping if our param was a **list**
      * default if one was provided and our call failed

    :raises:
      * :class:`stem.ControllerError` if the call fails and we weren't
        provided a default response
      * :class:`stem.InvalidArguments` if the 'params' requested was
        invalid
      * :class:`stem.ProtocolError` if the geoip database is known to be
        unavailable
    """

    start_time = time.time()
    reply = {}

    if isinstance(params, (bytes, unicode)):
      is_multiple = False
      params = set([params])
    else:
      if not params:
        return {}

      is_multiple = True
      params = set(params)

    # check for cached results

    from_cache = [param.lower() for param in params]
    cached_results = self._get_cache_map(from_cache, "getinfo")

    for key in cached_results:
      user_expected_key = _case_insensitive_lookup(params, key)
      reply[user_expected_key] = cached_results[key]
      params.remove(user_expected_key)

    for param in params:
      if param.startswith('ip-to-country/') and self.is_geoip_unavailable():
        # the geoip database already looks to be unavailable - abort the request
        if default == UNDEFINED:
          raise stem.ProtocolError("Tor geoip database is unavailable")
        else:
          return default

    # if everything was cached then short circuit making the query
    if not params:
      log.trace("GETINFO %s (cache fetch)" % " ".join(reply.keys()))

      if is_multiple:
        return reply
      else:
        return reply.values()[0]

    try:
      response = self.msg("GETINFO %s" % " ".join(params))
      stem.response.convert("GETINFO", response)
      response._assert_matches(params)

      # usually we want unicode values under python 3.x

      if stem.prereq.is_python_3() and not get_bytes:
        response.entries = dict((k, stem.util.str_tools._to_unicode(v)) for (k, v) in response.entries.items())

      reply.update(response.entries)

      if self.is_caching_enabled():
        to_cache = {}

        for key, value in response.entries.items():
          key = key.lower()  # make case insensitive

          if key in CACHEABLE_GETINFO_PARAMS:
            to_cache[key] = value
          elif key.startswith('ip-to-country/'):
            # both cache-able and means that we should reset the geoip failure count
            to_cache[key] = value
            self._geoip_failure_count = -1

        self._set_cache(to_cache, "getinfo")

      log.debug("GETINFO %s (runtime: %0.4f)" % (" ".join(params), time.time() - start_time))

      if is_multiple:
        return reply
      else:
        return reply.values()[0]
    except stem.ControllerError as exc:
      # bump geoip failure count if...
      # * we're caching results
      # * this was soley a geoip lookup
      # * we've never had a successful geoip lookup (failure count isn't -1)

      is_geoip_request = len(params) == 1 and list(params)[0].startswith('ip-to-country/')

      if is_geoip_request and self.is_caching_enabled() and self._geoip_failure_count != -1:
        self._geoip_failure_count += 1

        if self.is_geoip_unavailable():
          log.warn("Tor's geoip database is unavailable.")

      log.debug("GETINFO %s (failed: %s)" % (" ".join(params), exc))

      if default == UNDEFINED:
        raise exc
      else:
        return default

  def get_version(self, default = UNDEFINED):
    """
    A convenience method to get tor version that current controller is
    connected to.

    :param object default: response if the query fails

    :returns: :class:`~stem.version.Version` of the tor instance that we're
      connected to

    :raises:
      * :class:`stem.ControllerError` if unable to query the version
      * **ValueError** if unable to parse the version

      An exception is only raised if we weren't provided a default response.
    """

    try:
      version = self._get_cache("version")

      if not version:
        version = stem.version.Version(self.get_info("version"))
        self._set_cache({"version": version})

      return version
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        return default

  def get_exit_policy(self, default = UNDEFINED):
    """
    Effective ExitPolicy for our relay. This accounts for
    ExitPolicyRejectPrivate and default policies.

    :param object default: response if the query fails

    :returns: :class:`~stem.exit_policy.ExitPolicy` of the tor instance that
      we're connected to

    :raises:
      * :class:`stem.ControllerError` if unable to query the policy
      * **ValueError** if unable to parse the policy

      An exception is only raised if we weren't provided a default response.
    """
    with self._msg_lock:
      try:
        config_policy = self._get_cache("exit_policy")

        if not config_policy:
          policy = []

          if self.get_conf("ExitPolicyRejectPrivate") == "1":
            policy.append("reject private:*")

            public_addr = self.get_info("address", None)

            if public_addr:
              policy.append("reject %s:*" % public_addr)

          for policy_line in self.get_conf("ExitPolicy", multiple = True):
            policy += policy_line.split(",")

          policy += self.get_info("exit-policy/default").split(",")

          config_policy = stem.exit_policy.get_config_policy(policy)
          self._set_cache({"exit_policy": config_policy})

        return config_policy
      except Exception as exc:
        if default == UNDEFINED:
          raise exc
        else:
          return default

  def get_socks_listeners(self, default = UNDEFINED):
    """
    Provides the SOCKS **(address, port)** tuples that tor has open.

    :param object default: response if the query fails

    :returns: list of **(address, port)** tuples for the available SOCKS
      listeners

    :raises: :class:`stem.ControllerError` if unable to determine the listeners
      and no default was provided
    """

    try:
      proxy_addrs = []

      try:
        for listener in self.get_info("net/listeners/socks").split():
          if not (listener.startswith('"') and listener.endswith('"')):
            raise stem.ProtocolError("'GETINFO net/listeners/socks' responses are expected to be quoted: %s" % listener)
          elif not ':' in listener:
            raise stem.ProtocolError("'GETINFO net/listeners/socks' had a listener without a colon: %s" % listener)

          listener = listener[1:-1]  # strip quotes
          addr, port = listener.split(':')
          proxy_addrs.append((addr, port))
      except stem.InvalidArguments:
        # tor version is old (pre-tor-0.2.2.26-beta), use get_conf() instead
        socks_port = self.get_conf('SocksPort')

        for listener in self.get_conf('SocksListenAddress', multiple = True):
          if ':' in listener:
            addr, port = listener.split(':')
            proxy_addrs.append((addr, port))
          else:
            proxy_addrs.append((listener, socks_port))

      # validate that address/ports are valid, and convert ports to ints

      for addr, port in proxy_addrs:
        if not stem.util.connection.is_valid_ipv4_address(addr):
          raise stem.ProtocolError("Invalid address for a SOCKS listener: %s" % addr)
        elif not stem.util.connection.is_valid_port(port):
          raise stem.ProtocolError("Invalid port for a SOCKS listener: %s" % port)

      return [(addr, int(port)) for (addr, port) in proxy_addrs]
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        return default

  def get_protocolinfo(self, default = UNDEFINED):
    """
    A convenience method to get the protocol info of the controller.

    :param object default: response if the query fails

    :returns: :class:`~stem.response.protocolinfo.ProtocolInfoResponse` provided by tor

    :raises:
      * :class:`stem.ProtocolError` if the PROTOCOLINFO response is
        malformed
      * :class:`stem.SocketError` if problems arise in establishing or
        using the socket

      An exception is only raised if we weren't provided a default response.
    """

    import stem.connection

    try:
      return stem.connection.get_protocolinfo(self)
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        return default

  def get_user(self, default = UNDEFINED):
    """
    Provides the user tor is running as. This often only works if tor is
    running locally. Also, most of its checks are platform dependent, and hence
    are not entirely reliable.

    :param object default: response if the query fails

    :returns: str with the username tor is running as
    """

    user = self._get_cache("user")

    if not user:
      user = self.get_info("process/user", None)

    if not user and self.get_socket().is_localhost():
      pid = self.get_pid(None)

      if pid:
        user = stem.util.system.get_user(pid)

    if user:
      self._set_cache({"user": user})
      return user
    elif default == UNDEFINED:
      if self.get_socket().is_localhost():
        raise ValueError("Unable to resolve tor's user")
      else:
        raise ValueError("Tor isn't running locally")
    else:
      return default

  def get_pid(self, default = UNDEFINED):
    """
    Provides the process id of tor. This often only works if tor is running
    locally. Also, most of its checks are platform dependent, and hence are not
    entirely reliable.

    :param object default: response if the query fails

    :returns: int with our process' pid

    :raises: **ValueError** if unable to determine the pid and no default was
      provided
    """

    pid = self._get_cache("pid")

    if not pid:
      getinfo_pid = self.get_info("process/pid", None)

      if getinfo_pid and getinfo_pid.isdigit():
        pid = int(getinfo_pid)

    if not pid and self.get_socket().is_localhost():
      pid_file_path = self.get_conf("PidFile", None)

      if pid_file_path is not None:
        with open(pid_file_path) as pid_file:
          pid_file_contents = pid_file.read().strip()

          if pid_file_contents.isdigit():
            pid = int(pid_file_contents)

      if not pid:
        pid = stem.util.system.get_pid_by_name('tor')

      if not pid:
        control_socket = self.get_socket()

        if isinstance(control_socket, stem.socket.ControlPort):
          pid = stem.util.system.get_pid_by_port(control_socket.get_port())
        elif isinstance(control_socket, stem.socket.ControlSocketFile):
          pid = stem.util.system.get_pid_by_open_file(control_socket.get_socket_path())

    if pid:
      self._set_cache({"pid": pid})
      return pid
    elif default == UNDEFINED:
      if self.get_socket().is_localhost():
        raise ValueError("Unable to resolve tor's pid")
      else:
        raise ValueError("Tor isn't running locally")
    else:
      return default

  def get_microdescriptor(self, relay, default = UNDEFINED):
    """
    Provides the microdescriptor for the relay with the given fingerprint or
    nickname. If the relay identifier could be either a fingerprint *or*
    nickname then it's queried as a fingerprint.

    :param str relay: fingerprint or nickname of the relay to be queried
    :param object default: response if the query fails

    :returns: :class:`~stem.descriptor.microdescriptor.Microdescriptor` for the given relay

    :raises:
      * :class:`stem.ControllerError` if unable to query the descriptor
      * **ValueError** if **relay** doesn't conform with the pattern for being
        a fingerprint or nickname

      An exception is only raised if we weren't provided a default response.
    """

    try:
      if stem.util.tor_tools.is_valid_fingerprint(relay):
        query = "md/id/%s" % relay
      elif stem.util.tor_tools.is_valid_nickname(relay):
        query = "md/name/%s" % relay
      else:
        raise ValueError("'%s' isn't a valid fingerprint or nickname" % relay)

      desc_content = self.get_info(query, get_bytes = True)
      return stem.descriptor.microdescriptor.Microdescriptor(desc_content)
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        return default

  def get_microdescriptors(self, default = UNDEFINED):
    """
    Provides an iterator for all of the microdescriptors that tor presently
    knows about.

    **Tor does not expose this information via the control protocol**
    (:trac:`8323`). Until it does this reads the microdescriptors from disk,
    and hence won't work remotely or if we lack read permissions.

    :param list default: items to provide if the query fails

    :returns: iterates over
      :class:`~stem.descriptor.microdescriptor.Microdescriptor` for relays in
      the tor network

    :raises: :class:`stem.ControllerError` if unable to query tor and no
      default was provided
    """

    try:
      try:
        data_directory = self.get_conf("DataDirectory")
      except stem.ControllerError as exc:
        raise stem.OperationFailed(message = "Unable to determine the data directory (%s)" % exc)

      cached_descriptor_path = os.path.join(data_directory, "cached-microdescs")

      if not os.path.exists(data_directory):
        raise stem.OperationFailed(message = "Data directory reported by tor doesn't exist (%s)" % data_directory)
      elif not os.path.exists(cached_descriptor_path):
        raise stem.OperationFailed(message = "Data directory doens't contain cached microescriptors (%s)" % cached_descriptor_path)

      with stem.descriptor.reader.DescriptorReader([cached_descriptor_path]) as reader:
        for desc in reader:
          # It shouldn't be possible for these to be something other than
          # microdescriptors but as the saying goes: trust but verify.

          if not isinstance(desc, stem.descriptor.microdescriptor.Microdescriptor):
            raise stem.OperationFailed(message = "BUG: Descriptor reader provided non-microdescriptor content (%s)" % type(desc))

          yield desc
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        if default is not None:
          for entry in default:
            yield entry

  def get_server_descriptor(self, relay, default = UNDEFINED):
    """
    Provides the server descriptor for the relay with the given fingerprint or
    nickname. If the relay identifier could be either a fingerprint *or*
    nickname then it's queried as a fingerprint.

    **As of Tor version 0.2.3.25 relays no longer get server descriptors by
    default.** It's advised that you use microdescriptors instead, but if you
    really need server descriptors then you can get them by setting
    'UseMicrodescriptors 0'.

    :param str relay: fingerprint or nickname of the relay to be queried
    :param object default: response if the query fails

    :returns: :class:`~stem.descriptor.server_descriptor.RelayDescriptor` for the given relay

    :raises:
      * :class:`stem.ControllerError` if unable to query the descriptor
      * **ValueError** if **relay** doesn't conform with the pattern for being
        a fingerprint or nickname

      An exception is only raised if we weren't provided a default response.
    """

    try:
      if stem.util.tor_tools.is_valid_fingerprint(relay):
        query = "desc/id/%s" % relay
      elif stem.util.tor_tools.is_valid_nickname(relay):
        query = "desc/name/%s" % relay
      else:
        raise ValueError("'%s' isn't a valid fingerprint or nickname" % relay)

      desc_content = self.get_info(query, get_bytes = True)
      return stem.descriptor.server_descriptor.RelayDescriptor(desc_content)
    except Exception as exc:
      if default == UNDEFINED:
        if not self._is_server_descriptors_available():
          raise ValueError(SERVER_DESCRIPTORS_UNSUPPORTED)

        raise exc
      else:
        return default

  def get_server_descriptors(self, default = UNDEFINED):
    """
    Provides an iterator for all of the server descriptors that tor presently
    knows about.

    **As of Tor version 0.2.3.25 relays no longer get server descriptors by
    default.** It's advised that you use microdescriptors instead, but if you
    really need server descriptors then you can get them by setting
    'UseMicrodescriptors 0'.

    :param list default: items to provide if the query fails

    :returns: iterates over
      :class:`~stem.descriptor.server_descriptor.RelayDescriptor` for relays in
      the tor network

    :raises: :class:`stem.ControllerError` if unable to query tor and no
      default was provided
    """

    try:
      # TODO: We should iterate over the descriptors as they're read from the
      # socket rather than reading the whole thing into memory.
      #
      # https://trac.torproject.org/8248

      desc_content = self.get_info("desc/all-recent", get_bytes = True)

      if not desc_content and not self._is_server_descriptors_available():
        raise ValueError(SERVER_DESCRIPTORS_UNSUPPORTED)

      for desc in stem.descriptor.server_descriptor._parse_file(io.BytesIO(desc_content)):
        yield desc
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        if default is not None:
          for entry in default:
            yield entry

  def _is_server_descriptors_available(self):
    """
    Checks to see if tor server descriptors should be available or not.
    """

    return self.get_version() < stem.version.Requirement.MICRODESCRIPTOR_IS_DEFAULT or \
           self.get_conf('UseMicrodescriptors', None) == '0'

  def get_network_status(self, relay, default = UNDEFINED):
    """
    Provides the router status entry for the relay with the given fingerprint
    or nickname. If the relay identifier could be either a fingerprint *or*
    nickname then it's queried as a fingerprint.

    :param str relay: fingerprint or nickname of the relay to be queried
    :param object default: response if the query fails

    :returns: :class:`~stem.descriptor.router_status_entry.RouterStatusEntryV3`
      for the given relay

    :raises:
      * :class:`stem.ControllerError` if unable to query the descriptor
      * **ValueError** if **relay** doesn't conform with the pattern for being
        a fingerprint or nickname

      An exception is only raised if we weren't provided a default response.
    """

    # TODO: It would be great to add support for v3 router status entries. This
    # is pending...
    #
    # https://trac.torproject.org/7953

    try:
      if stem.util.tor_tools.is_valid_fingerprint(relay):
        query = "ns/id/%s" % relay
      elif stem.util.tor_tools.is_valid_nickname(relay):
        query = "ns/name/%s" % relay
      else:
        raise ValueError("'%s' isn't a valid fingerprint or nickname" % relay)

      desc_content = self.get_info(query, get_bytes = True)
      return stem.descriptor.router_status_entry.RouterStatusEntryV3(desc_content)
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        return default

  def get_network_statuses(self, default = UNDEFINED):
    """
    Provides an iterator for all of the router status entries that tor
    presently knows about.

    :param list default: items to provide if the query fails

    :returns: iterates over
      :class:`~stem.descriptor.router_status_entry.RouterStatusEntryV3` for
      relays in the tor network

    :raises: :class:`stem.ControllerError` if unable to query tor and no
      default was provided
    """

    try:
      # TODO: We should iterate over the descriptors as they're read from the
      # socket rather than reading the whole thing into memory.
      #
      # https://trac.torproject.org/8248

      desc_content = self.get_info("ns/all", get_bytes = True)

      desc_iterator = stem.descriptor.router_status_entry._parse_file(
        io.BytesIO(desc_content),
        True,
        entry_class = stem.descriptor.router_status_entry.RouterStatusEntryV3,
      )

      for desc in desc_iterator:
        yield desc
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        if default is not None:
          for entry in default:
            yield entry

  def get_conf(self, param, default = UNDEFINED, multiple = False):
    """
    Queries the current value for a configuration option. Some configuration
    options (like the ExitPolicy) can have multiple values. This provides a
    **list** with all of the values if **multiple** is **True**. Otherwise this
    will be a **str** with the first value.

    If provided with a **default** then that is provided if the configuration
    option was unset or the query fails (invalid configuration option, error
    response, control port closed, initiated, etc).

    If the configuration value is unset and no **default** was given then this
    provides **None** if **multiple** was **False** and an empty list if it was
    **True**.

    :param str param: configuration option to be queried
    :param object default: response if the option is unset or the query fails
    :param bool multiple: if **True** then provides a list with all of the
      present values (this is an empty list if the config option is unset)

    :returns:
      Response depends upon how we were called as follows...

      * **str** with the configuration value if **multiple** was **False**,
        **None** if it was unset
      * **list** with the response strings if multiple was **True**
      * default if one was provided and the configuration option was either
        unset or our call failed

    :raises:
      * :class:`stem.ControllerError` if the call fails and we weren't
        provided a default response
      * :class:`stem.InvalidArguments` if the configuration option
        requested was invalid
    """

    # Config options are case insensitive and don't contain whitespace. Using
    # strip so the following check will catch whitespace-only params.

    param = param.lower().strip()

    if not param:
      return default if default != UNDEFINED else None

    entries = self.get_conf_map(param, default, multiple)
    return _case_insensitive_lookup(entries, param, default)

  def get_conf_map(self, params, default = UNDEFINED, multiple = True):
    """
    Similar to :func:`~stem.control.Controller.get_conf` but queries multiple
    configuration options, providing back a mapping of those options to their
    values.

    There are three use cases for GETCONF:

      1. a single value is provided (e.g. **ControlPort**)
      2. multiple values are provided for the option (e.g. **ExitPolicy**)
      3. a set of options that weren't necessarily requested are returned (for
         instance querying **HiddenServiceOptions** gives **HiddenServiceDir**,
         **HiddenServicePort**, etc)

    The vast majority of the options fall into the first two categories, in
    which case calling :func:`~stem.control.Controller.get_conf` is sufficient.
    However, for batch queries or the special options that give a set of values
    this provides back the full response. As of tor version 0.2.1.25
    **HiddenServiceOptions** was the only option that falls into the third
    category.

    :param str,list params: configuration option(s) to be queried
    :param object default: value for the mappings if the configuration option
      is either undefined or the query fails
    :param bool multiple: if **True** then the values provided are lists with
      all of the present values

    :returns:
      **dict** of the 'config key => value' mappings. The value is a...

      * **str** if **multiple** is **False**, **None** if the configuration
        option is unset
      * **list** if **multiple** is **True**
      * the **default** if it was set and the value was either undefined or our
        lookup failed

    :raises:
      * :class:`stem.ControllerError` if the call fails and we weren't provided
        a default response
      * :class:`stem.InvalidArguments` if the configuration option requested
        was invalid
    """

    start_time = time.time()
    reply = {}

    if isinstance(params, (bytes, unicode)):
      params = [params]

    # remove strings which contain only whitespace
    params = filter(lambda entry: entry.strip(), params)

    if params == []:
      return {}

    # translate context sensitive options
    lookup_params = set([MAPPED_CONFIG_KEYS.get(entry, entry) for entry in params])

    # check for cached results

    from_cache = [param.lower() for param in lookup_params]
    cached_results = self._get_cache_map(from_cache, "getconf")

    for key in cached_results:
      user_expected_key = _case_insensitive_lookup(lookup_params, key)
      reply[user_expected_key] = cached_results[key]
      lookup_params.remove(user_expected_key)

    # if everything was cached then short circuit making the query
    if not lookup_params:
      log.trace("GETCONF %s (cache fetch)" % " ".join(reply.keys()))
      return self._get_conf_dict_to_response(reply, default, multiple)

    try:
      response = self.msg("GETCONF %s" % ' '.join(lookup_params))
      stem.response.convert("GETCONF", response)
      reply.update(response.entries)

      if self.is_caching_enabled():
        to_cache = dict((k.lower(), v) for k, v in response.entries.items())

        for key in UNCACHEABLE_GETCONF_PARAMS:
          if key in to_cache:
            del to_cache[key]

        self._set_cache(to_cache, "getconf")

      # Maps the entries back to the parameters that the user requested so the
      # capitalization matches (ie, if they request "exitpolicy" then that
      # should be the key rather than "ExitPolicy"). When the same
      # configuration key is provided multiple times this determines the case
      # based on the first and ignores the rest.
      #
      # This retains the tor provided camel casing of MAPPED_CONFIG_KEYS
      # entries since the user didn't request those by their key, so we can't
      # be sure what they wanted.

      for key in reply:
        if not key.lower() in MAPPED_CONFIG_KEYS.values():
          user_expected_key = _case_insensitive_lookup(params, key, key)

          if key != user_expected_key:
            reply[user_expected_key] = reply[key]
            del reply[key]

      log.debug("GETCONF %s (runtime: %0.4f)" % (" ".join(lookup_params), time.time() - start_time))
      return self._get_conf_dict_to_response(reply, default, multiple)
    except stem.ControllerError as exc:
      log.debug("GETCONF %s (failed: %s)" % (" ".join(lookup_params), exc))

      if default != UNDEFINED:
        return dict((param, default) for param in params)
      else:
        raise exc

  def _get_conf_dict_to_response(self, config_dict, default, multiple):
    """
    Translates a dictionary of 'config key => [value1, value2...]' into the
    return value of :func:`~stem.control.Controller.get_conf_map`, taking into
    account what the caller requested.
    """

    return_dict = {}

    for key, values in config_dict.items():
      if values == []:
        # config option was unset
        if default != UNDEFINED:
          return_dict[key] = default
        else:
          return_dict[key] = [] if multiple else None
      else:
        return_dict[key] = values if multiple else values[0]

    return return_dict

  def set_conf(self, param, value):
    """
    Changes the value of a tor configuration option. Our value can be any of
    the following...

    * a string to set a single value
    * a list of strings to set a series of values (for instance the ExitPolicy)
    * None to either set the value to 0/NULL

    :param str param: configuration option to be set
    :param str,list value: value to set the parameter to

    :raises:
      * :class:`stem.ControllerError` if the call fails
      * :class:`stem.InvalidArguments` if configuration options
        requested was invalid
      * :class:`stem.InvalidRequest` if the configuration setting is
        impossible or if there's a syntax error in the configuration values
    """

    self.set_options({param: value}, False)

  def reset_conf(self, *params):
    """
    Reverts one or more parameters to their default values.

    :param str params: configuration option to be reset

    :raises:
      * :class:`stem.ControllerError` if the call fails
      * :class:`stem.InvalidArguments` if configuration options requested was invalid
      * :class:`stem.InvalidRequest` if the configuration setting is
        impossible or if there's a syntax error in the configuration values
    """

    self.set_options(dict([(entry, None) for entry in params]), True)

  def set_options(self, params, reset = False):
    """
    Changes multiple tor configuration options via either a SETCONF or
    RESETCONF query. Both behave identically unless our value is None, in which
    case SETCONF sets the value to 0 or NULL, and RESETCONF returns it to its
    default value. This accepts str, list, or None values in a similar fashion
    to :func:`~stem.control.Controller.set_conf`. For example...

    ::

      my_controller.set_options({
        "Nickname": "caerSidi",
        "ExitPolicy": ["accept *:80", "accept *:443", "reject *:*"],
        "ContactInfo": "caerSidi-exit@someplace.com",
        "Log": None,
      })

    The params can optionally be a list of key/value tuples, though the only
    reason this type of argument would be useful is for hidden service
    configuration (those options are order dependent).

    :param dict,list params: mapping of configuration options to the values
      we're setting it to
    :param bool reset: issues a RESETCONF, returning **None** values to their
      defaults if **True**

    :raises:
      * :class:`stem.ControllerError` if the call fails
      * :class:`stem.InvalidArguments` if configuration options
        requested was invalid
      * :class:`stem.InvalidRequest` if the configuration setting is
        impossible or if there's a syntax error in the configuration values
    """

    start_time = time.time()

    # constructs the SETCONF or RESETCONF query
    query_comp = ["RESETCONF" if reset else "SETCONF"]

    if isinstance(params, dict):
      params = params.items()

    for param, value in params:
      if isinstance(value, str):
        query_comp.append("%s=\"%s\"" % (param, value.strip()))
      elif value:
        query_comp.extend(["%s=\"%s\"" % (param, val.strip()) for val in value])
      else:
        query_comp.append(param)

    query = " ".join(query_comp)
    response = self.msg(query)
    stem.response.convert("SINGLELINE", response)

    if response.is_ok():
      log.debug("%s (runtime: %0.4f)" % (query, time.time() - start_time))

      if self.is_caching_enabled():
        to_cache = {}

        for param, value in params:
          param = param.lower()

          if isinstance(value, (bytes, unicode)):
            value = [value]

          to_cache[param] = value

          if param == "exitpolicy":
            self._set_cache({"exitpolicy": None})

        self._set_cache(to_cache, "getconf")
    else:
      log.debug("%s (failed, code: %s, message: %s)" % (query, response.code, response.message))

      if response.code == "552":
        if response.message.startswith("Unrecognized option: Unknown option '"):
          key = response.message[37:response.message.find("\'", 37)]
          raise stem.InvalidArguments(response.code, response.message, [key])
        raise stem.InvalidRequest(response.code, response.message)
      elif response.code in ("513", "553"):
        raise stem.InvalidRequest(response.code, response.message)
      else:
        raise stem.ProtocolError("Returned unexpected status code: %s" % response.code)

  def add_event_listener(self, listener, *events):
    """
    Directs further tor controller events to a given function. The function is
    expected to take a single argument, which is a
    :class:`~stem.response.events.Event` subclass. For instance the following
    would print the bytes sent and received by tor over five seconds...

    ::

      import time
      from stem.control import Controller, EventType

      def print_bw(event):
        print "sent: %i, received: %i" % (event.written, event.read)

      with Controller.from_port(port = 9051) as controller:
        controller.authenticate()
        controller.add_event_listener(print_bw, EventType.BW)
        time.sleep(5)

    If a new control connection is initialized then this listener will be
    reattached.

    :param functor listener: function to be called when an event is received
    :param stem.control.EventType events: event types to be listened for

    :raises: :class:`stem.ProtocolError` if unable to set the events
    """

    # first checking that tor supports these event types
    with self._event_listeners_lock:
      if self.is_authenticated():
        for event_type in events:
          event_version = stem.response.events.EVENT_TYPE_TO_CLASS[event_type]._VERSION_ADDED

          if self.get_version() < event_version:
            raise stem.InvalidRequest(552, "%s event requires Tor version %s or later" % (event_type, event_version))

      for event_type in events:
        self._event_listeners.setdefault(event_type, []).append(listener)

      failed_events = self._attach_listeners()[1]

      # restricted the failures to just things we requested
      failed_events = set(failed_events).intersection(set(events))

      if failed_events:
        raise stem.ProtocolError("SETEVENTS rejected %s" % ", ".join(failed_events))

  def remove_event_listener(self, listener):
    """
    Stops a listener from being notified of further tor events.

    :param stem.control.EventListener listener: listener to be removed

    :raises: :class:`stem.ProtocolError` if unable to set the events
    """

    with self._event_listeners_lock:
      event_types_changed = False

      for event_type, event_listeners in self._event_listeners.items():
        if listener in event_listeners:
          event_listeners.remove(listener)

          if len(event_listeners) == 0:
            event_types_changed = True
            del self._event_listeners[event_type]

      if event_types_changed:
        response = self.msg("SETEVENTS %s" % " ".join(self._event_listeners.keys()))

        if not response.is_ok():
          raise stem.ProtocolError("SETEVENTS received unexpected response\n%s" % response)

  def _get_cache(self, param, namespace = None):
    """
    Queries our request cache for the given key.

    :param str param: key to be queried
    :param str namespace: namespace in which to check for the key

    :returns: cached value corresponding to key or **None** if the key wasn't found
    """

    return self._get_cache_map([param], namespace).get(param, None)

  def _get_cache_map(self, params, namespace = None):
    """
    Queries our request cache for multiple entries.

    :param list params: keys to be queried
    :param str namespace: namespace in which to check for the keys

    :returns: **dict** of 'param => cached value' pairs of keys present in cache
    """

    with self._cache_lock:
      cached_values = {}

      if self.is_caching_enabled():
        for param in params:
          if namespace:
            cache_key = "%s.%s" % (namespace, param)
          else:
            cache_key = param

          if cache_key in self._request_cache:
            cached_values[param] = self._request_cache[cache_key]

      return cached_values

  def _set_cache(self, params, namespace = None):
    """
    Sets the given request cache entries. If the new cache value is **None**
    then it is removed from our cache.

    :param dict params: **dict** of 'cache_key => value' pairs to be cached
    :param str namespace: namespace for the keys
    """

    with self._cache_lock:
      if not self.is_caching_enabled():
        return

      for key, value in params.items():
        if namespace:
          cache_key = "%s.%s" % (namespace, key)
        else:
          cache_key = key

        if value is None:
          if cache_key in self._request_cache:
            del self._request_cache[cache_key]
        else:
          self._request_cache[cache_key] = value

  def is_caching_enabled(self):
    """
    **True** if caching has been enabled, **False** otherwise.

    :returns: bool to indicate if caching is enabled
    """

    return self._is_caching_enabled

  def set_caching(self, enabled):
    """
    Enables or disables caching of information retrieved from tor.

    :param bool enabled: **True** to enable caching, **False** to disable it
    """

    self._is_caching_enabled = enabled

    if not self._is_caching_enabled:
      self.clear_cache()

  def clear_cache(self):
    """
    Drops any cached results.
    """

    with self._cache_lock:
      self._request_cache = {}
      self._geoip_failure_count = 0

  def load_conf(self, configtext):
    """
    Sends the configuration text to Tor and loads it as if it has been read from
    the torrc.

    :param str configtext: the configuration text

    :raises: :class:`stem.ControllerError` if the call fails
    """

    response = self.msg("LOADCONF\n%s" % configtext)
    stem.response.convert("SINGLELINE", response)

    if response.code in ("552", "553"):
      if response.code == "552" and response.message.startswith("Invalid config file: Failed to parse/validate config: Unknown option"):
        raise stem.InvalidArguments(response.code, response.message, [response.message[70:response.message.find('.', 70) - 1]])
      raise stem.InvalidRequest(response.code, response.message)
    elif not response.is_ok():
      raise stem.ProtocolError("+LOADCONF Received unexpected response\n%s" % str(response))

  def save_conf(self):
    """
    Saves the current configuration options into the active torrc file.

    :raises:
      * :class:`stem.ControllerError` if the call fails
      * :class:`stem.OperationFailed` if the client is unable to save
        the configuration file
    """

    response = self.msg("SAVECONF")
    stem.response.convert("SINGLELINE", response)

    if response.is_ok():
      return True
    elif response.code == "551":
      raise stem.OperationFailed(response.code, response.message)
    else:
      raise stem.ProtocolError("SAVECONF returned unexpected response code")

  def is_feature_enabled(self, feature):
    """
    Checks if a control connection feature is enabled. These features can be
    enabled using :func:`~stem.control.Controller.enable_feature`.

    :param str feature: feature to be checked

    :returns: **True** if feature is enabled, **False** otherwise
    """

    feature = feature.upper()

    if feature in self._enabled_features:
      return True
    else:
      # check if this feature is on by default
      defaulted_version = None

      if feature == "EXTENDED_EVENTS":
        defaulted_version = stem.version.Requirement.FEATURE_EXTENDED_EVENTS
      elif feature == "VERBOSE_NAMES":
        defaulted_version = stem.version.Requirement.FEATURE_VERBOSE_NAMES

      if defaulted_version:
        our_version = self.get_version(None)

        if our_version and our_version >= defaulted_version:
          self._enabled_features.append(feature)

      return feature in self._enabled_features

  def enable_feature(self, features):
    """
    Enables features that are disabled by default to maintain backward
    compatibility. Once enabled, a feature cannot be disabled and a new
    control connection must be opened to get a connection with the feature
    disabled. Feature names are case-insensitive.

    The following features are currently accepted:

      * EXTENDED_EVENTS - Requests the extended event syntax
      * VERBOSE_NAMES - Replaces ServerID with LongName in events and GETINFO results

    :param str,list features: a single feature or a list of features to be enabled

    :raises:
      * :class:`stem.ControllerError` if the call fails
      * :class:`stem.InvalidArguments` if features passed were invalid
    """

    if isinstance(features, (bytes, unicode)):
      features = [features]

    response = self.msg("USEFEATURE %s" % " ".join(features))
    stem.response.convert("SINGLELINE", response)

    if not response.is_ok():
      if response.code == "552":
        invalid_feature = []

        if response.message.startswith("Unrecognized feature \""):
          invalid_feature = [response.message[22:response.message.find("\"", 22)]]

        raise stem.InvalidArguments(response.code, response.message, invalid_feature)

      raise stem.ProtocolError("USEFEATURE provided an invalid response code: %s" % response.code)

    self._enabled_features += [entry.upper() for entry in features]

  def get_circuit(self, circuit_id, default = UNDEFINED):
    """
    Provides a circuit presently available from tor.

    :param int circuit_id: circuit to be fetched
    :param object default: response if the query fails

    :returns: :class:`stem.response.events.CircuitEvent` for the given circuit

    :raises:
      * :class:`stem.ControllerError` if the call fails
      * **ValueError** if the circuit doesn't exist

      An exception is only raised if we weren't provided a default response.
    """

    try:
      for circ in self.get_circuits():
        if circ.id == circuit_id:
          return circ

      raise ValueError("Tor presently does not have a circuit with the id of '%s'" % circuit_id)
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        return default

  def get_circuits(self, default = UNDEFINED):
    """
    Provides tor's currently available circuits.

    :param object default: response if the query fails

    :returns: **list** of :class:`stem.response.events.CircuitEvent` for our circuits

    :raises: :class:`stem.ControllerError` if the call fails and no default was provided
    """

    try:
      circuits = []
      response = self.get_info("circuit-status")

      for circ in response.splitlines():
        circ_message = stem.socket.recv_message(StringIO.StringIO("650 CIRC " + circ + "\r\n"))
        stem.response.convert("EVENT", circ_message, arrived_at = 0)
        circuits.append(circ_message)

      return circuits
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        return default

  def new_circuit(self, path = None, purpose = "general", await_build = False):
    """
    Requests a new circuit. If the path isn't provided, one is automatically
    selected.

    :param list,str path: one or more relays to make a circuit through
    :param str purpose: "general" or "controller"
    :param bool await_build: blocks until the circuit is built if **True**

    :returns: str of the circuit id of the newly created circuit

    :raises: :class:`stem.ControllerError` if the call fails
    """

    return self.extend_circuit('0', path, purpose, await_build)

  def extend_circuit(self, circuit_id = "0", path = None, purpose = "general", await_build = False):
    """
    Either requests the creation of a new circuit or extends an existing one.

    When called with a circuit value of zero (the default) a new circuit is
    created, and when non-zero the circuit with that id is extended. If the
    path isn't provided, one is automatically selected.

    A python interpreter session used to create circuits could look like this...

    ::

      >>> control.extend_circuit('0', ["718BCEA286B531757ACAFF93AE04910EA73DE617", "30BAB8EE7606CBD12F3CC269AE976E0153E7A58D", "2765D8A8C4BBA3F89585A9FFE0E8575615880BEB"])
      19
      >>> control.extend_circuit('0')
      20
      >>> print control.get_info('circuit-status')
      20 EXTENDED $718BCEA286B531757ACAFF93AE04910EA73DE617=KsmoinOK,$649F2D0ACF418F7CFC6539AB2257EB2D5297BAFA=Eskimo BUILD_FLAGS=NEED_CAPACITY PURPOSE=GENERAL TIME_CREATED=2012-12-06T13:51:11.433755
      19 BUILT $718BCEA286B531757ACAFF93AE04910EA73DE617=KsmoinOK,$30BAB8EE7606CBD12F3CC269AE976E0153E7A58D=Pascal1,$2765D8A8C4BBA3F89585A9FFE0E8575615880BEB=Anthracite PURPOSE=GENERAL TIME_CREATED=2012-12-06T13:50:56.969938

    :param str circuit_id: id of a circuit to be extended
    :param list,str path: one or more relays to make a circuit through, this is
      required if the circuit id is non-zero
    :param str purpose: "general" or "controller"
    :param bool await_build: blocks until the circuit is built if **True**

    :returns: str of the circuit id of the created or extended circuit

    :raises:
      * :class:`stem.InvalidRequest` if one of the parameters were invalid
      * :class:`stem.CircuitExtensionFailed` if we were waiting for the circuit
        to build but it failed
      * :class:`stem.ControllerError` if the call fails
    """

    # Attaches a temporary listener for CIRC events if we'll be waiting for it
    # to build. This is icky, but we can't reliably do this via polling since
    # we then can't get the failure if it can't be created.

    circ_queue, circ_listener = None, None

    if await_build:
      circ_queue = Queue.Queue()

      def circ_listener(event):
        circ_queue.put(event)

      self.add_event_listener(circ_listener, EventType.CIRC)

    try:
      # we might accidently get integer circuit ids
      circuit_id = str(circuit_id)

      if path is None and circuit_id == '0':
        path_opt_version = stem.version.Requirement.EXTENDCIRCUIT_PATH_OPTIONAL

        if not self.get_version() >= path_opt_version:
          raise stem.InvalidRequest(512, "EXTENDCIRCUIT requires the path prior to version %s" % path_opt_version)

      args = [circuit_id]

      if isinstance(path, (bytes, unicode)):
        path = [path]

      if path:
        args.append(",".join(path))

      if purpose:
        args.append("purpose=%s" % purpose)

      response = self.msg("EXTENDCIRCUIT %s" % " ".join(args))
      stem.response.convert("SINGLELINE", response)

      if response.code in ('512', '552'):
        raise stem.InvalidRequest(response.code, response.message)
      elif not response.is_ok():
        raise stem.ProtocolError("EXTENDCIRCUIT returned unexpected response code: %s" % response.code)

      if not response.message.startswith("EXTENDED "):
        raise stem.ProtocolError("EXTENDCIRCUIT response invalid:\n%s", response)

      new_circuit = response.message.split(" ", 1)[1]

      if await_build:
        while True:
          circ = circ_queue.get()

          if circ.id == new_circuit:
            if circ.status == CircStatus.BUILT:
              break
            elif circ.status == CircStatus.FAILED:
              raise stem.CircuitExtensionFailed("Circuit failed to be created: %s" % circ.reason, circ)
            elif circ.status == CircStatus.CLOSED:
              raise stem.CircuitExtensionFailed("Circuit was closed prior to build", circ)

      return new_circuit
    finally:
      if circ_listener:
        self.remove_event_listener(circ_listener)

  def repurpose_circuit(self, circuit_id, purpose):
    """
    Changes a circuit's purpose. Currently, two purposes are recognized...
      * general
      * controller

    :param str circuit_id: id of the circuit whose purpose is to be changed
    :param str purpose: purpose (either "general" or "controller")

    :raises: :class:`stem.InvalidArguments` if the circuit doesn't exist or if the purpose was invalid
    """

    response = self.msg("SETCIRCUITPURPOSE %s purpose=%s" % (circuit_id, purpose))
    stem.response.convert("SINGLELINE", response)

    if not response.is_ok():
      if response.code == "552":
        raise stem.InvalidRequest(response.code, response.message)
      else:
        raise stem.ProtocolError("SETCIRCUITPURPOSE returned unexpected response code: %s" % response.code)

  def close_circuit(self, circuit_id, flag = ''):
    """
    Closes the specified circuit.

    :param str circuit_id: id of the circuit to be closed
    :param str flag: optional value to modify closing, the only flag available
      is "IfUnused" which will not close the circuit unless it is unused

    :raises: :class:`stem.InvalidArguments` if the circuit is unknown
    :raises: :class:`stem.InvalidRequest` if not enough information is provided
    """

    response = self.msg("CLOSECIRCUIT %s %s" % (circuit_id, flag))
    stem.response.convert("SINGLELINE", response)

    if not response.is_ok():
      if response.code in ('512', '552'):
        if response.message.startswith("Unknown circuit "):
          raise stem.InvalidArguments(response.code, response.message, [circuit_id])
        raise stem.InvalidRequest(response.code, response.message)
      else:
        raise stem.ProtocolError("CLOSECIRCUIT returned unexpected response code: %s" % response.code)

  def get_streams(self, default = UNDEFINED):
    """
    Provides the list of streams tor is currently handling.

    :param object default: response if the query fails

    :returns: list of :class:`stem.response.events.StreamEvent` objects

    :raises: :class:`stem.ControllerError` if the call fails and no default was
      provided
    """

    try:
      streams = []
      response = self.get_info("stream-status")

      for stream in response.splitlines():
        message = stem.socket.recv_message(StringIO.StringIO("650 STREAM " + stream + "\r\n"))
        stem.response.convert("EVENT", message, arrived_at = 0)
        streams.append(message)

      return streams
    except Exception as exc:
      if default == UNDEFINED:
        raise exc
      else:
        return default

  def attach_stream(self, stream_id, circuit_id, exiting_hop = None):
    """
    Attaches a stream to a circuit.

    Note: Tor attaches streams to circuits automatically unless the
    __LeaveStreamsUnattached configuration variable is set to "1"

    :param str stream_id: id of the stream that must be attached
    :param str circuit_id: id of the circuit to which it must be attached
    :param int exiting_hop: hop in the circuit where traffic should exit

    :raises:
      * :class:`stem.InvalidRequest` if the stream or circuit id were unrecognized
      * :class:`stem.UnsatisfiableRequest` if the stream isn't in a state where it can be attached
      * :class:`stem.OperationFailed` if the stream couldn't be attached for any other reason
    """

    query = "ATTACHSTREAM %s %s" % (stream_id, circuit_id)

    if exiting_hop:
      query += " HOP=%s" % exiting_hop

    response = self.msg(query)
    stem.response.convert("SINGLELINE", response)

    if not response.is_ok():
      if response.code == '552':
        raise stem.InvalidRequest(response.code, response.message)
      elif response.code == '551':
        raise stem.OperationFailed(response.code, response.message)
      elif response.code == '555':
        raise stem.UnsatisfiableRequest(response.code, response.message)
      else:
        raise stem.ProtocolError("ATTACHSTREAM returned unexpected response code: %s" % response.code)

  def close_stream(self, stream_id, reason = stem.RelayEndReason.MISC, flag = ''):
    """
    Closes the specified stream.

    :param str stream_id: id of the stream to be closed
    :param stem.RelayEndReason reason: reason the stream is closing
    :param str flag: not currently used

    :raises: :class:`stem.InvalidArguments` if the stream or reason are not recognized
    :raises: :class:`stem.InvalidRequest` if the stream and/or reason are missing
    """

    # there's a single value offset between RelayEndReason.index_of() and the
    # value that tor expects since tor's value starts with the index of one

    response = self.msg("CLOSESTREAM %s %s %s" % (stream_id, stem.RelayEndReason.index_of(reason) + 1, flag))
    stem.response.convert("SINGLELINE", response)

    if not response.is_ok():
      if response.code in ('512', '552'):
        if response.message.startswith("Unknown stream "):
          raise stem.InvalidArguments(response.code, response.message, [stream_id])
        elif response.message.startswith("Unrecognized reason "):
          raise stem.InvalidArguments(response.code, response.message, [reason])
        raise stem.InvalidRequest(response.code, response.message)
      else:
        raise stem.ProtocolError("CLOSESTREAM returned unexpected response code: %s" % response.code)

  def signal(self, signal):
    """
    Sends a signal to the Tor client.

    :param stem.Signal signal: type of signal to be sent

    :raises: :class:`stem.InvalidArguments` if signal provided wasn't recognized
    """

    response = self.msg("SIGNAL %s" % signal)
    stem.response.convert("SINGLELINE", response)

    if not response.is_ok():
      if response.code == "552":
        raise stem.InvalidArguments(response.code, response.message, [signal])

      raise stem.ProtocolError("SIGNAL response contained unrecognized status code: %s" % response.code)

  def is_geoip_unavailable(self):
    """
    Provides **True** if we've concluded hat our geoip database is unavailable,
    **False** otherwise. This is determined by having our 'GETINFO
    ip-to-country/\*' lookups fail so this will default to **False** if we
    aren't making those queries.

    Geoip failures will be untracked if caching is disabled.

    :returns: **bool** to indicate if we've concluded our geoip database to be
      unavailable or not
    """

    return self._geoip_failure_count >= GEOIP_FAILURE_THRESHOLD

  def map_address(self, mapping):
    """
    Map addresses to replacement addresses. Tor replaces subseqent connections
    to the original addresses with the replacement addresses.

    If the original address is a null address, i.e., one of "0.0.0.0", "::0", or
    "." Tor picks an original address itself and returns it in the reply. If the
    original address is already mapped to a different address the mapping is
    removed.

    :param dict mapping: mapping of original addresses to replacement addresses

    :raises:
      * :class:`stem.InvalidRequest` if the addresses are malformed
      * :class:`stem.OperationFailed` if Tor couldn't fulfill the request

    :returns: **dict** with 'original -> replacement' address mappings
    """

    mapaddress_arg = " ".join(["%s=%s" % (k, v) for (k, v) in mapping.items()])
    response = self.msg("MAPADDRESS %s" % mapaddress_arg)
    stem.response.convert("MAPADDRESS", response)

    return response.entries

  def _post_authentication(self):
    super(Controller, self)._post_authentication()

    # try to re-attach event listeners to the new instance

    with self._event_listeners_lock:
      try:
        failed_events = self._attach_listeners()[1]

        if failed_events:
          # remove our listeners for these so we don't keep failing
          for event_type in failed_events:
            del self._event_listeners[event_type]

          logging_id = "stem.controller.event_reattach-%s" % "-".join(failed_events)
          log.log_once(logging_id, log.WARN, "We were unable to re-attach our event listeners to the new tor instance for: %s" % ", ".join(failed_events))
      except stem.ProtocolError as exc:
        log.warn("Unable to issue the SETEVENTS request to re-attach our listeners (%s)" % exc)

    # issue TAKEOWNERSHIP if we're the owning process for this tor instance

    owning_pid = self.get_conf("__OwningControllerProcess", None)

    if owning_pid == str(os.getpid()) and self.get_socket().is_localhost():
      response = self.msg("TAKEOWNERSHIP")
      stem.response.convert("SINGLELINE", response)

      if response.is_ok():
        # Now that tor is tracking our ownership of the process via the control
        # connection, we can stop having it check for us via our pid.

        try:
          self.reset_conf("__OwningControllerProcess")
        except stem.ControllerError as exc:
          log.warn("We were unable to reset tor's __OwningControllerProcess configuration. It will continue to periodically check if our pid exists. (%s)" % exc)
      else:
        log.warn("We were unable assert ownership of tor through TAKEOWNERSHIP, despite being configured to be the owning process through __OwningControllerProcess. (%s)" % response)

  def _handle_event(self, event_message):
    stem.response.convert("EVENT", event_message, arrived_at = time.time())

    with self._event_listeners_lock:
      for event_type, event_listeners in self._event_listeners.items():
        if event_type == event_message.type:
          for listener in event_listeners:
            listener(event_message)

  def _attach_listeners(self):
    """
    Attempts to subscribe to the self._event_listeners events from tor. This is
    a no-op if we're not presently authenticated.

    :returns: tuple of the form (set_events, failed_events)

    :raises: :class:`stem.ControllerError` if unable to make our request to tor
    """

    set_events, failed_events = [], []

    with self._event_listeners_lock:
      if self.is_authenticated():
        # try to set them all
        response = self.msg("SETEVENTS %s" % " ".join(self._event_listeners.keys()))

        if response.is_ok():
          set_events = self._event_listeners.keys()
        else:
          # One of the following likely happened...
          #
          # * Our user attached listeners before having an authenticated
          #   connection, so we couldn't check if we met the version
          #   requirement.
          #
          # * User attached listeners to one tor instance, then connected us to
          #   an older tor instancce.
          #
          # * Some other controller hiccup (far less likely).
          #
          # See if we can set some subset of our events.

          for event in self._event_listeners.keys():
            response = self.msg("SETEVENTS %s" % " ".join(set_events + [event]))

            if response.is_ok():
              set_events.append(event)
            else:
              failed_events.append(event)

    return (set_events, failed_events)


def _parse_circ_path(path):
  """
  Parses a circuit path as a list of **(fingerprint, nickname)** tuples. Tor
  circuit paths are defined as being of the form...

  ::

    Path = LongName *("," LongName)
    LongName = Fingerprint [ ( "=" / "~" ) Nickname ]

    example:
    $999A226EBED397F331B612FE1E4CFAE5C1F201BA=piyaz

  ... *unless* this is prior to tor version 0.2.2.1 with the VERBOSE_NAMES
  feature turned off (or before version 0.1.2.2 where the feature was
  introduced). In that case either the fingerprint or nickname in the tuple
  will be **None**, depending on which is missing.

  ::

    Path = ServerID *("," ServerID)
    ServerID = Nickname / Fingerprint

    example:
    $E57A476CD4DFBD99B4EE52A100A58610AD6E80B9,hamburgerphone,PrivacyRepublic14

  :param str path: circuit path to be parsed

  :returns: list of **(fingerprint, nickname)** tuples, fingerprints do not have a proceeding '$'

  :raises: :class:`stem.ProtocolError` if the path is malformed
  """

  if path:
    try:
      return [_parse_circ_entry(entry) for entry in path.split(',')]
    except stem.ProtocolError as exc:
      # include the path with the exception
      raise stem.ProtocolError("%s: %s" % (exc, path))
  else:
    return []


def _parse_circ_entry(entry):
  """
  Parses a single relay's 'LongName' or 'ServerID'. See the
  :func:`~_stem.control._parse_circ_path` function for more information.

  :param str entry: relay information to be parsed

  :returns: **(fingerprint, nickname)** tuple

  :raises: :class:`stem.ProtocolError` if the entry is malformed
  """

  if '=' in entry:
    # common case
    fingerprint, nickname = entry.split('=')
  elif '~' in entry:
    # this is allowed for by the spec, but I've never seen it used
    fingerprint, nickname = entry.split('~')
  elif entry[0] == '$':
    # old style, fingerprint only
    fingerprint, nickname = entry, None
  else:
    # old style, nickname only
    fingerprint, nickname = None, entry

  if fingerprint is not None:
    if not stem.util.tor_tools.is_valid_fingerprint(fingerprint, True):
      raise stem.ProtocolError("Fingerprint in the circuit path is malformed (%s)" % fingerprint)

    fingerprint = fingerprint[1:]  # strip off the leading '$'

  if nickname is not None and not stem.util.tor_tools.is_valid_nickname(nickname):
    raise stem.ProtocolError("Nickname in the circuit path is malformed (%s)" % nickname)

  return (fingerprint, nickname)


def _case_insensitive_lookup(entries, key, default = UNDEFINED):
  """
  Makes a case insensitive lookup within a list or dictionary, providing the
  first matching entry that we come across.

  :param list,dict entries: list or dictionary to be searched
  :param str key: entry or key value to look up
  :param object default: value to be returned if the key doesn't exist

  :returns: case insensitive match or default if one was provided and key wasn't found

  :raises: **ValueError** if no such value exists
  """

  if entries is not None:
    if isinstance(entries, dict):
      for k, v in entries.items():
        if k.lower() == key.lower():
          return v
    else:
      for entry in entries:
        if entry.lower() == key.lower():
          return entry

  if default != UNDEFINED:
    return default
  else:
    raise ValueError("key '%s' doesn't exist in dict: %s" % (key, entries))
