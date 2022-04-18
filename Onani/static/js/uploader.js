/*
 * @Author: kapsikkum
 * @Date:   2020-10-12 02:03:30
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-18 15:46:06
 */
const fileInput = document.getElementById("file-upload"),
  uploadButton = document.getElementById("upload-button"),
  sourceInput = document.getElementById("file-source"),
  tagTextarea = document.getElementById("file-tags"),
  uploaderForm = document.getElementById("uploader-form");

// New file reader for the image
const reader = new FileReader();

// array to store images in
let imageList;

function displayImage(input) {
  "use strict";
  if (input.files && input.files[0]) {
    // Set the imageList to the input files
    imageList = input.files;

    reader.onload = function (e) {
      // Set the onload funtion to update the preview image
      document.getElementById("preview-image").src = e.target.result;
    };

    // Read the first file in the input files
    reader.readAsDataURL(input.files[0]);
  }
}

function hideOtherSlides(slideName) {
  for (let element of document.getElementsByClassName("uploader-panel")) {
    if (element.id != slideName) {
      element.style.display = "none";
    } else {
      element.style.display = "flex";
    }
  }
}

function slide1() {
  // Update the title
  document.getElementById("uploader-title-text").innerText = "Select Files";

  // update the buttons
  document.getElementById("left-button").style.visibility = "hidden";
  document.getElementById("right-button").style.visibility = "visible";
  document.getElementById("right-button").onclick = () => {
    slide2();
  };
  document.getElementById("upload-button").style.display = "none";
  document.getElementById("right-button").style.display = "block";
  // Make all other slides invisible
  hideOtherSlides("first-panel");
}

function slide2() {
  // Update the title
  document.getElementById("uploader-title-text").innerText = "Select Tags";

  // update the buttons
  document.getElementById("left-button").style.visibility = "visible";
  document.getElementById("left-button").onclick = () => {
    slide1();
  };
  document.getElementById("right-button").style.visibility = "visible";
  document.getElementById("right-button").onclick = () => {
    slide3();
  };
  document.getElementById("right-button").style.display = "block";
  document.getElementById("upload-button").style.display = "none";
  // Make all other slides invisible
  hideOtherSlides("second-panel");
}

function slide3() {
  // Update the title
  document.getElementById("uploader-title-text").innerText =
    "Extra Information";

  // update the buttons
  document.getElementById("left-button").style.visibility = "visible";
  document.getElementById("left-button").onclick = () => {
    slide2();
  };
  document.getElementById("right-button").style.display = "none";
  document.getElementById("upload-button").style.display = "block";

  // Make all other slides invisible
  hideOtherSlides("third-panel");
}

function invokeForm() {
  if (fileInput.files.length === 0) {
    slide1();
    alert("Please select some files!");
  } else {
    uploaderForm.submit();
  }
}
