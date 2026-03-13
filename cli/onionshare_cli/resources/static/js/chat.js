$(function() {
  const chatContainerEls = document.getElementsByClassName("chat-container");
  for (const chatContainerEl of chatContainerEls) {
    chatContainerEl.classList.remove("no-js");
  }

  const socket = io(`${location.origin}/chat`, { transports: ["websocket"] });

  // Store current username received from app context
  /** @type {HTMLInputElement} */
  const usernameEl = document.getElementById("username");
  var current_username = usernameEl.value.trim();

  // Triggered on any status change by any user, such as some
  // user joined, or changed username, or left, etc.
  socket.on('status', function (data) {
    addMessageToPanel(data, current_username, 'status');
    console.log(data, current_username);
  });

  // Triggered when message is received from a user. Even when sent
  // by self, it get triggered after the server sends back the emit.
  socket.on('chat_message', function (data) {
    addMessageToPanel(data, current_username, 'chat');
    console.log(data, current_username);
  });

  // Triggered when disconnected either by server stop or timeout
  socket.on('disconnect', function (_reason, _details) {
    addMessageToPanel({ 'msg': 'The chat server is disconnected.' }, current_username, 'status');
  })
  socket.on('connect_error', function (error) {
    console.error(error);
  })

  // Trigger new message on enter or click of send message button.
  document.getElementById('new-message').addEventListener('keypress', function (e) {
    if (e.key === "Enter") {
      emitMessage(socket);
    }
  });

  // Keep buttons disabled unless changed or not empty
  usernameEl.addEventListener('keyup', function (event) {
    const username = event.currentTarget.value;
    if (username !== '' && username !== current_username) {
      if (event.key === "Enter") {
        this.blur();
        current_username = updateUsername(socket) || current_username;
      }
    }
  });

  // Show warning of losing data
  window.addEventListener("beforeunload", function (e) {
    e.preventDefault();
  });
});

const addMessageToPanel = function (data, current_username, messageType) {
  const scrollDiff = getScrollDiffBefore();
  if (messageType === 'status') {
    addStatusMessage(data.msg);
    if (data.connected_users) {
      addUserList(data.connected_users, current_username);
    }
  } else if (messageType === 'chat') {
    addChatMessage(data.username, data.msg)
  }
  scrollBottomMaybe(scrollDiff);
}

const emitMessage = function (socket) {
  const newMessageEl = document.getElementById("new-message");
  const newMessage = newMessageEl.value;
  newMessageEl.value = '';

  const chatEl = document.getElementById("chat");
  // $(chatEl).scrollTop(chatEl.scrollHeight);
  chatEl.scrollTo({top: chatEl.scrollHeight });

  socket.emit('text', { msg: newMessage });
}

const updateUsername = function (socket) {
  const username = document.getElementById("username").value;

  if (!checkUsernameExists(username) && !checkUsernameTooLong(username) && !checkUsernameAscii(username)) {
    fetch(`${location.origin}/update-session-username`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 'username': username }),
    }).then(function (response) {
      console.log(response);
      return response.json();
    }).then(function (response) {
      console.log(response);
      if (response.success && response.username == username) {
        socket.emit('update_username', { username: username });
      } else {
        throw new Error("Failed to update username.");
      }
    }).catch(function() {
      addStatusMessage("Failed to update username.");
    });

    return username;
  }
  return false;
}

/************************************/
/********* Util Functions ***********/
/************************************/

/**
 * @param username {string}
 * @returns {boolean}
 */
const checkUsernameAscii = function (username) {
  // ASCII characters have code points in the range U+0000-U+007F.
  const usernameErrorEl = document.getElementById("username-error");
  usernameErrorEl.textContent = '';

  if (!/^[\u0000-\u007f]*$/.test(username)) {
    usernameErrorEl.textContent = 'Non-ASCII usernames are not supported.';
    return true;
  }

  return false;
}

/**
 * @param username {string}
 * @returns {boolean}
 */
const checkUsernameExists = function (username) {
  const usernameErrorEl = document.getElementById("username-error");
  usernameErrorEl.textContent = '';

  const userEls = document.querySelectorAll("#user-list li");
  const userMatches = Array.from(userEls).some(function(el) {
    return el.textContent === username;
  });

  if (userMatches) {
    usernameErrorEl.textContent = 'User with that username exists!';
  }

  return userMatches;
}

/**
 * @param username {string}
 * @returns {boolean}
 */
const checkUsernameTooLong = function (username) {
  const usernameErrorEl = document.getElementById("username-error");
  usernameErrorEl.textContent = '';

  if (username.length > 128) {
    usernameErrorEl.textContent = 'Please choose a shorter username.';
    return true;
  }

  return false;
}

/**
 * @returns {number}
 */
const getScrollDiffBefore = function () {
  const chatEl = document.getElementById("chat");
  return chatEl.scrollTop - (chatEl.scrollHeight - chatEl.offsetHeight);
}

/**
 * @param scrollDiff {number}
 */
const scrollBottomMaybe = function (scrollDiff) {
  // Scrolls to bottom if the user is scrolled at bottom
  // if the user has scrolled up, it won't scroll at bottom.
  // Note: when a user themselves send a message, it will still
  // scroll to the bottom even if they had scrolled up before.
  const chatEl = document.getElementById("chat");
  if (scrollDiff > 0) {
    // $(chatEl).scrollTop(chatEl.scrollHeight);
    chatEl.scrollTo({top: chatEl.scrollHeight });
  }
}

/**
 * @param message {string}
 */
const addStatusMessage = function (message) {
  const messageEl = document.createElement('p');
  messageEl.outerHTML = `<p class="status"></p>`;

  messageEl.getElementsByClassName("status")[0].textContent = message;

  document.getElementById("chat").appendChild(messageEl);
}

/**
 * @param username {string}
 * @param message {string}
 */
const addChatMessage = function (username, message) {
  const messageEl = document.createElement('p');
  messageEl.outerHTML = `<p><span class="username"></span><span class="message"></span></p>`;

  messageEl.getElementsByClassName("username")[0].textContent = username;
  messageEl.getElementsByClassName("message")[0].textContent = message;

  document.getElementById("chat").appendChild(messageEl);
}

/**
 * @param connected_users {string[]}
 * @param current_username {string}
 */
const addUserList = function (connected_users, current_username) {
  connected_users.sort();

  const liList = connected_users.filter(function (username) {
    return (username !== current_username);
  }).map(function (username) {
    const li = document.createElement('p');
    li.textContent = username;
    return li;
  });

  const userListEl = document.getElementById("user-list");
  userListEl.replaceChildren(...liList);
}
