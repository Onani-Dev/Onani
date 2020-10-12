/*
 * @Author: kapsikkum
 * @Date:   2020-10-12 02:03:30
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2020-10-12 23:08:46
 */
const fileInput = document.getElementById("file-upload"),
  uploadButton = document.getElementById("upload-button"),
  sourceInput = document.getElementById("file-source"),
  tagTextarea = document.getElementById("file-tags"),
  ratingRadios = document.getElementsByName("rating");

function getRating() {
  for (let i = 0; i < ratingRadios.length; i++) {
    if (ratingRadios[i].checked)
      return ratingRadios[i].value;
  }
}

function displayImage(input) {
  if (input.files && input.files[0]) {
    var reader = new FileReader();

    reader.onload = function (e) {
      $('#preview-image').attr('src', e.target.result);
    };

    reader.readAsDataURL(input.files[0]);
  }
}

uploadButton.onclick = function () {
  if (fileInput.files.length <= 0) {
    alert("Please select a file to upload.");
    return;
  }
  let formdata = new FormData();
  formdata.append("file", fileInput.files[0]);
  formdata.append("source", sourceInput.value);
  formdata.append("tags", tagTextarea.value.replace(/ /g, "_").split("\n"));
  formdata.append("rating", getRating());

  fetch("/api/upload", {
    method: 'POST',
    body: formdata
  }).then(response => response.json())
    .then(result => {
      if (result.ok) {
        location.href = result.path;
      }
      else {
        alert(result.error);
      }
    })
    .catch(error => alert(error));
}