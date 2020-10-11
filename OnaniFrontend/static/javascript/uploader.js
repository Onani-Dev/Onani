/*
 * @Author: kapsikkum
 * @Date:   2020-10-12 02:03:30
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2020-10-12 02:43:02
 */
const fileInput = document.getElementById("file-upload"),
  uploadButton = document.getElementById("upload-button");

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
  formdata.append("source", "http://10.147.20.97:5000/");
  formdata.append("tags", "http://10.147.20.97:5000/");

  fetch("/api/upload", {
    method: 'POST',
    body: formdata,
    redirect: 'follow'
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