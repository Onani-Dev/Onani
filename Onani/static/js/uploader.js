/*
 * @Author: kapsikkum
 * @Date:   2020-10-12 02:03:30
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-19 03:47:25
 */
const fileInput = document.getElementById("file-upload"),
  previewImage = document.getElementById("preview-image"),
  uploaderForm = document.getElementById("uploader-form");

// New file reader for the images
// const reader = new FileReader();

// array to store images in
let imageList;

// Image elements to paginate
let imageElements = [];
let currentImage = 0;

// Image
function displayImage(input) {
  "use strict";
  if (input.files && input.files[0]) {
    currentImage = 0;
    imageElements = [];

    // Set the imageList to the input files
    imageList = input.files;
    // Promises array
    let promises = [];
    // Read all the files
    for (let file of imageList) {
      let filePromise = new Promise((resolve) => {
        let reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
      });
      promises.push(filePromise);
    }

    // Complete all the promises and add the results to the slick slider
    Promise.all(promises).then((fileContents) => {
      for (let file of fileContents) {
        let previewImage = document.createElement("img");
        previewImage.className = "preview-image";
        previewImage.src = file;
        imageElements.push(previewImage);
      }
      changeImage(imageElements[currentImage]);
    });
  }
}

function changeImage(image) {
  previewImage.replaceChildren(image);
  // previewImage.appendChild(image);
}

document.getElementById("left-button-image").onclick = () => {
  currentImage -= 1;
  changeImage(imageElements[currentImage]);
};

document.getElementById("right-button-image").onclick = () => {
  currentImage += 1;
  changeImage(imageElements[currentImage]);
};

// Slides
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
