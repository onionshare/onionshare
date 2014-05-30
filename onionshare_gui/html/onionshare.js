function send(msg) {
    document.title = "null";
    document.title = msg;
}

function set_basename(basename) {
    $('#basename').html(basename);
}

function set_strings(strings) {
    strings = JSON.parse(strings)
    $('#give-this-url').html(strings['give_this_url'])
}
