function send(msg) {
  document.title = "null";
  document.title = msg;
}

function init(basename, strings) {
  $('#basename').html(basename).show();
}

function url_is_set() {
  $('#copy-button')
    .click(function(){
      send('copy_url');
    })
    .show();
}

function update(msg) {
  var $line = $('<p></p>').append(msg);
  $('#output').append($line);
  
  // scroll to bottom
  $('#output').scrollTop($('#output').height());
}
