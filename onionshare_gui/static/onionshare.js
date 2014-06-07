$(function(){
  onionshare = {}

  function update($msg) {
    var $line = $('<p></p>').append($msg);
    $('#output').append($line);
    
    // scroll to bottom
    $('#output').scrollTop($('#output').height());
  }

  function linebreak() {
    update($('<hr>'));
  }

  function copy_to_clipboard() {
    $.ajax({
      url: '/copy_url',
      success: function(data, textStatus, jqXHR){
        update('Copied secret URL to clipboard.');
      }
    });
  }
  $('#copy-button').click(copy_to_clipboard);

  // start onionshare
  $.ajax({
    url: '/start_onionshare',
    success: function(data, textStatus, jqXHR){
      onionshare = JSON.parse(data);

      $('#basename').html(onionshare.basename);
      update("Sharing file: "+onionshare.basename+" ("+onionshare.filesize+" bytes)");
      update("SHA1 checksum: "+onionshare.filehash);
      linebreak();
      update(onionshare.strings['give_this_url']);
      update($('<strong>').html(onionshare.url));
      linebreak();
      copy_to_clipboard();
      $('#copy-button').show();

      $('#loading').hide();
      $('#content').show();
    }
  });

});
