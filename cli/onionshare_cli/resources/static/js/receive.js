$(function () {
  // Add a flash message
  const flash = function (category, message) {
    const li = document.createElement("li");
    li.className = category;
    li.textContent = message;
    document.getElementById("flashes").append(li);
  };

  const scriptSrc = document.getElementById("receive-script").src;
  const staticImgPath = scriptSrc
    .substr(0, scriptSrc.lastIndexOf("/") + 1)
    .replace("js", "img");

  const sendEl = document.getElementById("send");

  // Intercept submitting the form
  sendEl.addEventListener("submit", function (event) {
    event.preventDefault();

    // Build the form data
    const formData = new FormData();

    // Files
    const filenames = [];
    const fileSelectEl = document.getElementById("file-select");
    if (fileSelectEl !== null) {
      for (const file of fileSelectEl.files) {
        filenames.push(file.name);
        formData.append("file[]", file, file.name);
      }
    }

    // Text message
    const textEl = document.getElementById("text");
    if (textEl !== null) {
      formData.append("text", text.value);
    }

    // Reset the upload form
    sendEl.reset();

    // Don't use jQuery for ajax request, because the upload progress event doesn't
    // have access to the the XMLHttpRequest object
    const ajax = new XMLHttpRequest();

    ajax.upload.addEventListener(
      "progress",
      function (event) {
        // Update progress bar for this specific upload
        if (event.lengthComputable) {
          const progressEl = ajax.uploadDivEl.querySelector("progress");
          progressEl.setAttribute("value", event.loaded);
          progressEl.setAttribute("max", event.total);
        }

        // All data has been sent to the first Tor node but has not yet traversed
        // the full onion circuit to the receiver. Switch the progress bar to
        // indeterminate so the user understands the transfer is still in progress,
        // and warn them not to close the tab.
        if (event.loaded === event.total) {
          ajax.uploadDivEl.querySelector(".cancel").remove();
          ajax.uploadDivEl.querySelector(".upload-status").innerHTML =
            '<img src="' +
            staticImgPath +
            '/ajax.gif" alt="" /> ' +
            "Sending &mdash; waiting for data to traverse the Tor network &hellip;";
          ajax.uploadDivEl.querySelector(".upload-warning").classList.remove("hidden");
        }
      },
      false,
    );

    ajax.addEventListener(
      "load",
      function (_event) {
        // Remove the upload div
        ajax.uploadDivEl.remove();

        // Parse response
        try {
          const response = JSON.parse(ajax.response);

          // The 'new_body' response replaces the whole HTML document and ends
          if ("new_body" in response) {
            document.body.innerHTML = response["new_body"];
            return;
          }

          // Show error flashes
          const errors = response["error_flashes"] || [];
          for (const error of errors) {
            flash("error", error);
          }

          // Show info flashes
          const infos = response["info_flashes"] || [];
          for (const info of infos) {
            flash("info", info);
          }
        } catch (e) {
          flash("error", "Invalid response from server: " + data);
        }
      },
      false,
    );

    ajax.addEventListener(
      "error",
      function (_event) {
        flash("error", "Error uploading: " + filenames.join(", "));

        // Remove the upload div
        ajax.uploadDivEl.remove();
      },
      false,
    );

    ajax.addEventListener(
      "abort",
      function (_event) {
        flash("error", "Upload aborted: " + filenames.join(", "));
      },
      false,
    );

    // Make the upload div

    /*  The DOM for an upload looks something like this:
    <div class="upload">
      <div class="upload-meta">
        <input class="cancel" type="button" value="Cancel" />
        <div class="upload-filename">educational-video.mp4, secret-plans.pdf</div>
        <div class="upload-status">Sending data to initial Tor node ...</div>
        <div class="upload-warning" style="display:none">Do not close this tab ...</div>
      </div>
      <progress value="25" max="100"></progress>
    </div>
    Once all bytes reach the first Tor node, 'value' is removed from <progress>
    (making it indeterminate), the warning div is shown, and the cancel button
    is removed. */

    // Warning shown only once data has cleared the first hop and is traversing the circuit.
    // Hidden by default; revealed in the progress handler above.
    const uploadDivEl = document.createElement("div");
    uploadDivEl.classList.add("upload");
    uploadDivEl.innerHTML = `
      <div class="upload-meta">
        <input class="cancel" type="button" value="Cancel" />
        <div class="upload-filename"></div>
        <div class="upload-status">Sending data to initial Tor node ...</div>
        <div class="upload-warning hidden">Do not close this tab until the submission is complete.</div>
      </div>
      <progress value="0" max="100"></progress>
    `;

    uploadDivEl.querySelector("div.upload-filename").textContent =
      filenames.join(", ");

    uploadDivEl
      .querySelector("input.cancel")
      .addEventListener("click", function () {
        // Abort the upload, and remove the upload div
        ajax.abort();
        uploadDivEl.remove();
      });

    document.getElementById("uploads").append(uploadDivEl);

    ajax.uploadDivEl = uploadDivEl;

    // Send the request
    ajax.open("POST", "/upload-ajax", true);
    ajax.send(formData);
  });
});
