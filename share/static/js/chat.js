$(function(){
  var socket;
  var last_username;
  var username_list = [];
  $(document).ready(function(){
    socket = io.connect('http://' + document.domain + ':' + location.port + '/chat');
    var current_username = $('#username').val();
    socket.on('connect', function() {
      socket.emit('joined', {});
    });
    socket.on('status', function(data) {
      $('#chat').append('<p><small><i>' + sanitizeHTML(data.msg) + '</i></small></p>');
      if (data.user && current_username !== data.user) {
        $('#user-list').append('<li>' + sanitizeHTML(data.user) + '</li>')
        username_list.push(data.user);
      }
      if (data.new_name && current_username !== data.new_name) {
        last_username = current_username;
        current_username = data.new_name;
        username_list[username_list.indexOf(last_username)] = current_username;
        $('#user-list li').each(function(key, value) {
          if ($(value).text() === data.old_name) {
            $(value).html(sanitizeHTML(current_username));
          }
        })
      }
      $('#chat').scrollTop($('#chat')[0].scrollHeight);
    });
    socket.on('update_list', function(data) {
      if (username_list.indexOf(data.name) === -1 &&
        current_username !== data.name &&
        last_username !== data.name
      ) {
        username_list.push(data.name);
        $('#user-list').append('<li>' + sanitizeHTML(data.name) + '</li>')
      }
      $('#chat').scrollTop($('#chat')[0].scrollHeight);
    });
    socket.on('message', function(data) {
      $('#chat').append('<p>' + sanitizeHTML(data.msg) + '</p>');
      $('#chat').scrollTop($('#chat')[0].scrollHeight);
    });
    $('#new-message').on('keypress', function(e) {
      var code = e.keyCode || e.which;
      if (code == 13) {
        emitMessage(socket);
      }
    });
    $('#send-button').on('click', emitMessage);
    $('#update-username').on('click', function() {
      var username = $('#username').val();
      socket.emit('update_username', {username: username});
    });
  });
});

var emitMessage = function(socket) {
  var text = $('#new-message').val();
  $('#new-message').val('');
  socket.emit('text', {msg: text});
}

var sanitizeHTML = function(str) {
	var temp = document.createElement('span');
	temp.textContent = str;
	return temp.innerHTML;
};
