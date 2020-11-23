$(function () {
  $(document).ready(function () {
    $('.chat-container').removeClass('no-js');
    var socket = io.connect(
      'http://' + document.domain + ':' + location.port + '/chat',
      {
        transports: ['websocket']
      }
    );

    // Store current username received from app context
    var current_username = $('#username').val();

    // On browser connect, emit a socket event to be added to 
    // room and assigned random username
    socket.on('connect', function () {
      socket.emit('joined', {});
    });

    // Triggered on any status change by any user, such as some
    // user joined, or changed username, or left, etc.
    socket.on('status', function (data) {
      addMessageToRoom(data, current_username, 'status');
      console.log(data, current_username);
    });

    // Triggered when message is received from a user. Even when sent
    // by self, it get triggered after the server sends back the emit.
    socket.on('message', function (data) {
      addMessageToRoom(data, current_username, 'chat');
      console.log(data, current_username);
    });

    // Triggered when disconnected either by server stop or timeout
    socket.on('disconnect', function (data) {
      addMessageToRoom({ 'msg': 'The chat server is disconnected.' }, current_username, 'status');
    })
    socket.on('connect_error', function (error) {
      console.log("error");
    })

    // Trigger new message on enter or click of send message button.
    $('#new-message').on('keypress', function (e) {
      var code = e.keyCode || e.which;
      if (code == 13) {
        emitMessage(socket);
      }
    });

    // Keep buttons disabled unless changed or not empty
    $('#username').on('keyup', function (event) {
      if ($('#username').val() !== '' && $('#username').val() !== current_username) {
        if (event.keyCode == 13 || event.which == 13) {
          this.blur();
          current_username = updateUsername(socket) || current_username;
        }
      }
    });

    // Show warning of losing data
    $(window).on('beforeunload', function (e) {
      e.preventDefault();
      e.returnValue = '';
      return '';
    });
  });
});

var addMessageToRoom = function (data, current_username, messageType) {
  var scrollDiff = getScrollDiffBefore();
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

var emitMessage = function (socket) {
  var text = $('#new-message').val();
  $('#new-message').val('');
  $('#chat').scrollTop($('#chat')[0].scrollHeight);
  socket.emit('text', { msg: text });
}

var updateUsername = function (socket) {
  var username = $('#username').val();
  if (!checkUsernameExists(username)) {
    $.ajax({
      method: 'POST',
      url: `http://${document.domain}:${location.port}/update-session-username`,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify({ 'username': username })
    }).done(function (response) {
      console.log(response);
      if (response.success && response.username == username) {
        socket.emit('update_username', { username: username });
      }
    });
    return username;
  }
  return false;
}

/************************************/
/********* Util Functions ***********/
/************************************/

var createUserListHTML = function (connected_users, current_user) {
  var userListHTML = '';
  connected_users.sort();
  connected_users.forEach(function (username) {
    if (username !== current_user) {
      userListHTML += `<li>${sanitizeHTML(username)}</li>`;
    }
  });
  return userListHTML;
}

var checkUsernameExists = function (username) {
  $('#username-error').text('');
  var userMatches = $('#user-list li').filter(function () {
    return $(this).text() === username;
  });
  if (userMatches.length) {
    $('#username-error').text('User with that username exists!');
    return true;
  }
  return false;
}

var getScrollDiffBefore = function () {
  return $('#chat').scrollTop() - ($('#chat')[0].scrollHeight - $('#chat')[0].offsetHeight);
}

var scrollBottomMaybe = function (scrollDiff) {
  // Scrolls to bottom if the user is scrolled at bottom
  // if the user has scrolled upp, it wont scroll at bottom.
  // Note: when a user themselves send a message, it will still
  // scroll to the bottom even if they had scrolled up before.
  if (scrollDiff > 0) {
    $('#chat').scrollTop($('#chat')[0].scrollHeight);
  }
}

var addStatusMessage = function (message) {
  $('#chat').append(
    `<p class="status">${sanitizeHTML(message)}</p>`
  );
}

var addChatMessage = function (username, message) {
  $('#chat').append(`<p><span class="username">${sanitizeHTML(username)}</span><span class="message">${sanitizeHTML(message)}</span></p>`);
}

var addUserList = function (connected_users, current_username) {
  $('#user-list').html(
    createUserListHTML(
      connected_users,
      current_username
    )
  );
}

var sanitizeHTML = function (str) {
  var temp = document.createElement('span');
  temp.textContent = str;
  return temp.innerHTML;
};
