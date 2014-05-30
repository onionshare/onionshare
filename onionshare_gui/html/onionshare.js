function send(msg) {
    document.title = "null";
    document.title = msg;
}

function init(basename, strings) {
    $('#basename').html(basename);
    $('#give-this-url').html(strings['give_this_url'])
}

function set_url(url) {
  $('#url').html(url);
  $('#url-wrapper').slideDown(200);
}

function update(msg) {
    $('#output').append($('<p></p>').html(msg))
}
