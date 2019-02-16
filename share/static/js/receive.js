$(function(){
  // Add a flash message
  var flash = function(category, message) {
    $('#flashes').append($('<li>').addClass(category).text(message));
  };

  // Add an upload
  var new_upload_div = function(xhr, filenames) {
    /*
    The DOM for an upload looks something like this:

    <div class="upload">
      <div class="upload-meta">
        <input class="cancel" type="button" value="Cancel" />
        <div class="upload-filename">educational-video.mp4, secret-plans.pdf</div>
        <div class="upload-status">Sending to first Tor node ...</div>
      </div>
      <progress value="25" max="100"></progress>
    </div>
    */
    var $progress = $('<progress>').attr({ value: '0', max: 100 });
    var $cancel_button = $('<input>').addClass('cancel').attr({ type: 'button', value: 'Cancel' });
    var $upload_filename = $('<div>').addClass('upload-filename').text(filenames.join(', '));
    var $upload_status = $('<div>').addClass('upload-status').text('Sending data to initial Tor node ...');

    var $upload_div = $('<div>').addClass('upload')
      .append(
        $('<div>').addClass('upload-meta')
          .append($cancel_button)
          .append($upload_filename)
          .append($upload_status)
      )
      .append($progress);

    $cancel_button.click(function(){
      // Abort the upload, and remove the upload div
      xhr.abort();
      $upload_div.remove()
    });

    return $upload_div;
  };

  // Intercept submitting the form
  $('#send').submit(function(event){
    event.preventDefault();

    // Create form data, and list of filenames
    var files = $('#file-select').get(0).files;
    var filenames = [];
    var formData = new FormData();
    for(var i = 0; i < files.length; i++) {
      var file = files[i];
      filenames.push(file.name);
      formData.append('file[]', file, file.name);
    }

    // Reset the upload form
    $('#send').get(0).reset();

    // Start upload
    xhr = $.ajax({
      method: 'POST',
      url: window.location.pathname + '/upload-ajax',
      data: formData,
      // Tell jQuery not to process data or worry about content-type
      cache: false,
      contentType: false,
      processData: false,
      // Custom XMLHttpRequest
      xhr: function() {
        var xhr = $.ajaxSettings.xhr();
        if(xhr.upload) {
          xhr.upload.addEventListener('progress', function(event) {
            // Update progress bar for this specific upload
            if(event.lengthComputable) {
              console.log('upload progress', ''+event.loaded+' bytes / '+event.total+' bytes');
              $('progress', this.$upload_div).attr({
                value: event.loaded,
                max: event.total,
              });
            }

            // If it's finished sending all data to the first Tor node, remove cancel button
            // and update the status
            if(event.loaded == event.total) {
              console.log('upload progress', 'complete');
              $('.cancel', this.$upload_div).remove();
              $('.upload-status', this.$upload_div).html('<img src="/static/img/ajax.gif" alt="" /> Waiting for data to finish traversing Tor network ...');
            }
          }, false);
        }
        return xhr;
      },
      success: function(data, textStatus, xhr){
        console.log('upload finished', data);

        // Remove the upload div
        xhr.$upload_div.remove();

        // Parse response
        try {
          var response = JSON.parse(data);

          // The 'new_body' response replaces the whole HTML document and ends
          if('new_body' in response) {
            $('body').html(response['new_body']);
            return;
          }

          // Show error flashes
          if('error_flashes' in response) {
            for(var i=0; i<response['error_flashes'].length; i++) {
              flash('error', response['error_flashes'][i]);
            }
          }

          // Show info flashes
          if('info_flashes' in response) {
            for(var i=0; i<response['info_flashes'].length; i++) {
              flash('info', response['info_flashes'][i]);
            }
          }
        } catch(e) {
          console.log('invalid response');
          flash('error', 'Invalid response from server: '+data);
        }
      },
      error: function(xhr, textStatus, errorThrown){
        console.log('error', errorThrown);
        flash('error', 'Error uploading: ' + errorThrown);
      }
    });
    console.log('upload started', filenames);

    // Make the upload div
    xhr.$upload_div = new_upload_div(xhr, filenames);
    $('#uploads').append(xhr.$upload_div);
  });
});
