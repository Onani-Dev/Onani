/*
 * @Author: kapsikkum
 * @Date:   2020-10-12 02:03:30
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-03-19 14:56:52
 */
"use strict";

const fileInput = document.getElementById("file-upload"),
  uploadButton = document.getElementById("upload-button"),
  sourceInput = document.getElementById("file-source"),
  tagTextarea = document.getElementById("file-tags"),
  ratingRadios = document.getElementsByName("rating");

// New file reader for the image
const reader = new FileReader();

// array to store images in
let imageList;

function displayImage(input) {
  if (input.files && input.files[0]) {
    // Set the imageList to the input files
    imageList = input.files;

    reader.onload = function (e) {
      // Set the onload funtion to a jQuery function to update the preview image
      $("#preview-image").attr("src", e.target.result);
    };

    // Read the first file in the input files
    reader.readAsDataURL(input.files[0]);
  }
}
