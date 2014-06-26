$(function(){
  var onionshare = {}

  function update($msg) {
    var $line = $('<li>').append($msg);
    $('#log').prepend($line);
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
      url: '/heartbeat',
      success: function(data, textStatus, jqXHR){
        if(data != '') {
          var events = JSON.parse(data);
          for(var i=0; i<events.length; i++) {
            var r = events[i];

            if(r.type == REQUEST_LOAD) {
              update($('<span>').addClass('weblog').html(onionshare.strings['download_page_loaded']));
            } else if(r.type == REQUEST_DOWNLOAD) {
              var $download = $('<span>')
                .attr('id', 'download-'+r.data.id)
                .addClass('weblog').html(onionshare.strings['download_started'])
                .append($('<span>').addClass('progress'));
              update($download);
            } else if(r.type == REQUEST_PROGRESS) {
              // is the download complete?
              if(r.data.bytes == onionshare.filesize) {
                $('#download-'+r.data.id).html(onionshare.strings['download_finished']);

                // close on finish?
                if($('#close-on-finish').is(':checked')) {
                  function close_countdown(i) {
                    $('#close-countdown').html(onionshare.strings['close_countdown'].replace('{0}', i));
                    if(i == 0) {
                      // close program
                      $.ajax({ url: '/close' });
                    } else {
                      // continue countdown
                      setTimeout(function(){ close_countdown(i-1) }, 1000);
                    }
                  }
                  update($('<span>').attr('id', 'close-countdown'));
                  close_countdown(3);
                }
              }
              // still in progress
              else {
                var percent = Math.floor((r.data.bytes / onionshare.filesize) * 100);
                $('#download-'+r.data.id+' .progress').html(' '+human_readable_filesize(r.data.bytes)+', '+percent+'%');
              }
            } else {
              if(r.path != '/favicon.ico')
                update($('<span>').addClass('weblog-error').html(onionshare.strings['other_page_loaded']+': '+r.path));
            }
          }
        }

        setTimeout(check_for_requests, 1000);
      }
    });
  }

  $('#close-on-finish').change(function(){
    if($('#close-on-finish').is(':checked')) {
      $.ajax({ url: '/stay_open_false' });
    } else {
      $.ajax({ url: '/stay_open_true' });
    }
  });

  // initialize
  $.ajax({
    url: '/init_info',
    success: function(data, textStatus, jqXHR){
      onionshare = JSON.parse(data);

      $('#basename').html(onionshare.basename);
      $('#filesize .label').html(onionshare.strings['filesize']+':');
      $('#filehash .label').html(onionshare.strings['sha1_checksum']+':');
      $('#close-on-finish-wrapper label').html(onionshare.strings['close_on_finish']);
      $('#loading .calculating').html(onionshare.strings['calculating_sha1']);

      if(onionshare.stay_open) {
        $('#close-on-finish').removeAttr('checked');
      }
      
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
