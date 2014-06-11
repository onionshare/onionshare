$(function(){
  var onionshare = {}

  function update($msg) {
    var $line = $('<li>').append($msg);
    $('#log').append($line);
    
    // scroll to bottom
    $('#log').scrollTop($('#log').height());
  }

  function copy_to_clipboard() {
    $.ajax({
      url: '/copy_url',
      success: function(data, textStatus, jqXHR){
        update(onionshare.strings['copied_url']);
      }
    });
  }
  $('#copy-button').click(copy_to_clipboard);

  var REQUEST_LOAD = 0;
  var REQUEST_DOWNLOAD = 1;
  var REQUEST_PROGRESS = 2;
  var REQUEST_OTHER = 3;
  function check_for_requests() {
    $.ajax({
      url: '/check_for_requests',
      success: function(data, textStatus, jqXHR){
        if(data != '') {
          var r = JSON.parse(data);
          if(r.type == REQUEST_LOAD) {
            update($('<span>').addClass('weblog').html(onionshare.strings['download_page_loaded']));
          } else if(r.type == REQUEST_DOWNLOAD) {
            var $download = $('<span>')
              .attr('id', 'download-'+r.data.id)
              .addClass('weblog').html(onionshare.strings['download_started'])
              .append($('<span>').addClass('progress'));
            update($download);
          } else if(r.type == REQUEST_PROGRESS) {
              var percent = Math.floor((r.data.bytes / onionshare.filesize) * 100);
              $('#download-'+r.data.id+' .progress').html(' '+human_readable_filesize(r.data.bytes)+', '+percent+'%');
          } else {
            if(r.path != '/favicon.ico')
              update($('<span>').addClass('weblog-error').html(onionshare.strings['other_page_loaded']+': '+r.path));
          }
        }

        setTimeout(check_for_requests, 1000);
      }
    });
  }

  // initialize
  $.ajax({
    url: '/init_info',
    success: function(data, textStatus, jqXHR){
      onionshare = JSON.parse(data);

      $('#basename').html(onionshare.basename);
      $('#filesize .label').html(onionshare.strings['filesize']+':');
      $('#filehash .label').html(onionshare.strings['sha1_checksum']+':');
      $('#loading .calculating').html(onionshare.strings['calculating_sha1']);
      
      // after getting the initial info, start the onionshare server
      $.ajax({
        url: '/start_onionshare',
        success: function(data, textStatus, jqXHR){
          var data_obj = JSON.parse(data);
          onionshare.filehash = data_obj.filehash;
          onionshare.filesize = data_obj.filesize;
          onionshare.url = data_obj.url;

          $('#loading').remove();

          $('#filesize .value').html(human_readable_filesize(onionshare.filesize));
          $('#filehash .value').html(onionshare.filehash);
          $('#filesize').show(500);
          $('#filehash').show(500);

          update('<span>'+onionshare.strings['give_this_url']+'</span><br/><strong>'+onionshare.url+'</strong>');
          copy_to_clipboard();
          $('#copy-button').show();

          setTimeout(check_for_requests, 1000);
        }
      });
    }
  });
});
