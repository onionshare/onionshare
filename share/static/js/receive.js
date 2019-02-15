// Hide the noscript div, because our javascript is executing
document.getElementById('noscript').style.display = 'none';

var form = document.getElementById('send');
var fileSelect = document.getElementById('file-select');
var uploadButton = document.getElementById('send-button');
var flashes = document.getElementById('flashes');

// Add a flash message
function flash(category, message) {
  var el = document.createElement('li');
  el.innerText = message;
  el.className = category;
  flashes.appendChild(el);
}

form.onsubmit = function(event) {
  event.preventDefault();

  // Disable button, and update text
  uploadButton.innerHTML = 'Uploading ...';
  uploadButton.disabled = true;
  fileSelect.disabled = true;

  // Create form data
  var files = fileSelect.files;
  var formData = new FormData();
  for (var i = 0; i < files.length; i++) {
    var file = files[i];
    formData.append('file[]', file, file.name);
  }

  // Set up the request
  var ajax = new XMLHttpRequest();

  ajax.upload.addEventListener('progress', function(event){
    console.log('upload progress', 'uploaded '+event.loaded+' bytes / '+event.total+' bytes');
    var percent = parseInt((event.loaded / event.total) * 100, 10);
    uploadButton.innerHTML = 'Uploading '+percent+'%';
  }, false);

  ajax.addEventListener('load', function(event){
    console.log('upload finished', ajax.response);
    if(ajax.status == 200) {
      // Parse response
      try {
        var response = JSON.parse(ajax.response);

        // The 'new_body' response replaces the whole HTML document and ends
        if('new_body' in response) {
          document.body.innerHTML = response['new_body'];
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
        console.log('invalid response', ajax.response);
        flash('error', 'Invalid response from server: '+ajax.response);
      }

      // Re-enable button, and update text
      uploadButton.innerHTML = 'Send Files';
      uploadButton.disabled = false;
      fileSelect.disabled = false;
    }
  }, false);

	ajax.addEventListener('error', function(event){
    console.log('error', event);
    flash('error', 'Error uploading');
  }, false);

  ajax.addEventListener('abort', function(event){
    console.log('abort', event);
    flash('error', 'Upload aborted');
  }, false);

  // Send the request
  ajax.open('POST', window.location.pathname + '/upload-ajax', true);
  ajax.send(formData);
  console.log('upload started');
}
