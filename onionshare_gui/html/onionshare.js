function send(msg) {
    document.title = "null";
    document.title = msg;
}

function init(basename, strings) {
    $('#basename').html(basename);
}

function url_is_set() {
    $('#copy-button')
        .click(function(){
            send('copy_url');
        })
        .show();
}

function update(msg) {
    $('#output').append($('<p></p>').html(msg))
    
    // scroll to bottom
    $('#output').scrollTop($('#output').height());
}
