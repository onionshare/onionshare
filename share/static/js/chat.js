$(function(){
  $(document).ready(function(){
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/chat');

    // Store current username received from app context
    var current_username = $('#username').val();

    // On browser connect, emit a socket event to be added to 
    // room and assigned random username
    socket.on('connect', function() {
      socket.emit('joined', {});
    });

    // Triggered on any status change by any user, such as some
    // user joined, or changed username, or left, etc.
    socket.on('status', function(data) {
      addMessageToRoom(data, current_username, 'status');
    });

    // Triggered when message is received from a user. Even when sent
    // by self, it get triggered after the server sends back the emit.
    socket.on('message', function(data) {
      addMessageToRoom(data, current_username, 'chat');
    });

    // Trigger new message on enter or click of send message button.
    $('#new-message').on('keypress', function(e) {
      var code = e.keyCode || e.which;
      if (code == 13) {
        emitMessage(socket);
      }
    });
    $('#send-button').on('click', function(e) {
      emitMessage(socket);
    });

    // Update username
    $('#update-username').on('click', function() {
      var username = $('#username').val();
      current_username = username;
      socket.emit('update_username', {username: username});
    });

    // Show warning of losing data
    $(window).on('beforeunload', function (e) {
      e.preventDefault();
      e.returnValue = '';
      return '';
    });
  });
});

var addMessageToRoom = function(data, current_username, messageType) {
  var scrollDiff = getScrollDiffBefore();
  if (messageType === 'status') {
    addStatusMessage(data.msg);
    if (data.connected_users) {
      addUserList(data.connected_users, current_username);
    }
  } else if (messageType === 'chat') {
    addChatMessage(data.msg)
  }
  scrollBottomMaybe(scrollDiff);
}

var emitMessage = function(socket) {
  var text = $('#new-message').val();
  $('#new-message').val('');
  $('#chat').scrollTop($('#chat')[0].scrollHeight);
  socket.emit('text', {msg: text});
}

/************************************/
/********* Util Functions ***********/
/************************************/

var createUserListHTML = function(connected_users, current_user) {
  var userListHTML = '';
  connected_users.sort();
  connected_users.forEach(function(username) {
    if (username !== current_user) {
      userListHTML += `<li>${sanitizeHTML(username)}</li>`;
    }
  });
  return userListHTML;
}

var getScrollDiffBefore = function() {
  return $('#chat').scrollTop() - ($('#chat')[0].scrollHeight - $('#chat')[0].offsetHeight);
}

var scrollBottomMaybe = function(scrollDiff) {
  // Scrolls to bottom if the user is scrolled at bottom
  // if the user has scrolled upp, it wont scroll at bottom.
  // Note: when a user themselves send a message, it will still
  // scroll to the bottom even if they had scrolled up before.
  if (scrollDiff > 0) {
    $('#chat').scrollTop($('#chat')[0].scrollHeight);
  }
}

var addStatusMessage = function(message) {
  $('#chat').append(
    `<p><small><i>${sanitizeHTML(message)}</i></small></p>`
  );
}

var addChatMessage = function(message) {
  $('#chat').append(`<p>${sanitizeHTML(message)}</p>`);
}

var addUserList = function(connected_users, current_username) {
  $('#user-list').html(
    createUserListHTML(
      connected_users,
      current_username
    )
  );
}

var sanitizeHTML = function(str) {
	var temp = document.createElement('span');
	temp.textContent = str;
	return temp.innerHTML;
};
