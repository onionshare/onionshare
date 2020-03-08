$(function(){
  var socket;
  $(document).ready(function(){
    socket = io.connect('http://' + document.domain + ':' + location.port + '/chat');
    socket.on('connect', function() {
      socket.emit('joined', {});
    });
    socket.on('status', function(data) {
      console.log("received")
      $('#chat').append('<p><small><i>' + data.msg + '</i></small></p>');
      $('#chat').scrollTop($('#chat')[0].scrollHeight);
    });
    socket.on('message', function(data) {
      $('#chat').append('<p>' + data.msg + '</p>');
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

function emitMessage(socket) {
  text = $('#new-message').val();
  $('#new-message').val('');
  socket.emit('text', {msg: text});
}
