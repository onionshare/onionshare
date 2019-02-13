var form = document.getElementById('send');
var fileSelect = document.getElementById('file-select');
var uploadButton = document.getElementById('send-button');

form.onsubmit = function(event) {
  event.preventDefault();

  // Update button text.
  uploadButton.innerHTML = 'Uploading...';

  // Get the selected files from the input.
  var files = fileSelect.files;

  // Create a new FormData object.
  var formData = new FormData();

  // Loop through each of the selected files.
  for (var i = 0; i < files.length; i++) {
    var file = files[i];

    // Add the file to the request.
    formData.append('file[]', file, file.name);
  }

  // Set up the request.
  var xhr = new XMLHttpRequest();

  // Open the connection.
  xhr.open('POST', window.location.pathname + '/upload', true);

  xhr.onload = function() {
      if (xhr.status == 200) {
          uploadButton.innerHTML = 'Send Files';
      }
  }

  // Send the Data.
  xhr.send(formData);
}

