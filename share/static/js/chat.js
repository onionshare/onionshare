$(function(){
  var socket;
  $(document).ready(function(){
    socket = io.connect('http://' + document.domain + ':' + location.port + '/chat');
    socket.on('connect', function() {
      socket.emit('joined', {});
    });
    socket.on('status', function(data) {
      $('#chat').append('<p><small><i>' + sanitizeHTML(data.msg) + '</i></small></p>');
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
  });
});

var emitMessage = function(socket) {
  text = $('#new-message').val();
  $('#new-message').val('');
  socket.emit('text', {msg: text});
}

var sanitizeHTML = function(str) {
	var temp = document.createElement('span');
	temp.textContent = str;
	return temp.innerHTML;
};
