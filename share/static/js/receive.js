// Hide the noscript div, because our javascript is executing
document.getElementById('noscript').style.display = 'none';

var form = document.getElementById('send');
var fileSelect = document.getElementById('file-select');
var uploadButton = document.getElementById('send-button');

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

  ajax.addEventListener("load", function(event){
    console.log("upload finished");
    if(ajax.status == 200) {
      // Re-enable button, and update text
      uploadButton.innerHTML = 'Send Files';
      uploadButton.disabled = false;
      fileSelect.disabled = false;
    }
  }, false);

	ajax.addEventListener("error", function(event){
    console.log('error', event);
  }, false);

  ajax.addEventListener("abort", function(event){
    console.log('abort', event);
  }, false);

  // Send the request
  ajax.open('POST', window.location.pathname + '/upload', true);
  ajax.send(formData);
  console.log("upload started");
}
