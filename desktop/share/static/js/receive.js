$(function(){
  // Add a flash message
  var flash = function(category, message) {
    $('#flashes').append($('<li>').addClass(category).text(message));
  };

  var scriptSrc = document.getElementById('receive-script').src;
  var staticImgPath = scriptSrc.substr(0, scriptSrc.lastIndexOf( '/' )+1).replace('js', 'img');

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

    // Don't use jQuery for ajax request, because the upload progress event doesn't
    // have access to the the XMLHttpRequest object
    var ajax = new XMLHttpRequest();

    ajax.upload.addEventListener('progress', function(event){
      // Update progress bar for this specific upload
      if(event.lengthComputable) {
        $('progress', ajax.$upload_div).attr({
          value: event.loaded,
          max: event.total,
        });
      }

      // If it's finished sending all data to the first Tor node, remove cancel button
      // and update the status
      if(event.loaded == event.total) {
        $('.cancel', ajax.$upload_div).remove();
        $('.upload-status', ajax.$upload_div).html('<img src="' + staticImgPath + '/ajax.gif" alt="" /> Waiting for data to finish traversing Tor network ...');
      }
    }, false);

    ajax.addEventListener('load', function(event){
      // Remove the upload div
      ajax.$upload_div.remove();

      // Parse response
      try {
        var response = JSON.parse(ajax.response);

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
        flash('error', 'Invalid response from server: '+data);
      }
    }, false);

    ajax.addEventListener('error', function(event){
      flash('error', 'Error uploading: '+filenames.join(', '));

      // Remove the upload div
      ajax.$upload_div.remove()
    }, false);

    ajax.addEventListener('abort', function(event){
      flash('error', 'Upload aborted: '+filenames.join(', '));
    }, false);

    // Make the upload div

    /*  The DOM for an upload looks something like this:
    <div class="upload">
      <div class="upload-meta">
        <input class="cancel" type="button" value="Cancel" />
        <div class="upload-filename">educational-video.mp4, secret-plans.pdf</div>
        <div class="upload-status">Sending to first Tor node ...</div>
      </div>
      <progress value="25" max="100"></progress>
    </div> */
    var $progress = $('<progress>').attr({ value: '0', max: 100 });
    var $cancel_button = $('<input>').addClass('cancel').attr({ type: 'button', value: 'Cancel' });
    var $upload_filename = $('<div>').addClass('upload-filename').text(filenames.join(', '));
    var $upload_status = $('<div>').addClass('upload-status').text('Sending data to initial Tor node ...');

    var $upload_div = $('<div>')
      .addClass('upload')
      .append(
        $('<div>').addClass('upload-meta')
          .append($cancel_button)
          .append($upload_filename)
          .append($upload_status)
      )
      .append($progress);

    $cancel_button.click(function(){
      // Abort the upload, and remove the upload div
      ajax.abort();
      $upload_div.remove()
    });

    ajax.$upload_div = $upload_div;
    $('#uploads').append($upload_div);

    // Send the request
    ajax.open('POST', '/upload-ajax', true);
    ajax.send(formData);
  });
});
