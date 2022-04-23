/**
 * @Author: kapsikkum
 * @Date:   2022-04-21 14:56:40
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-23 21:53:01
 */
import { Pagination } from "./utils.min.js";

class PostUpload {
  constructor() {
    // Slides
    this.uploaderSlides = new Pagination(
      document.getElementsByClassName("uploader-panel")
    );

    document.getElementById("right-button").onclick = () => {
      this.switchSlide(this.uploaderSlides.next);
    };
    document.getElementById("left-button").onclick = () => {
      this.switchSlide(this.uploaderSlides.prev);
    };

    document.getElementById("upload-button").onclick = () => {
      this.invokeForm();
    };

    // Image controls
    document.getElementById("left-button-image").onclick = () => {
      if (this.imagePages.hasPrev) {
        this.changeImage(this.imagePages.prev);
      }
    };

    document.getElementById("right-button-image").onclick = () => {
      if (this.imagePages.hasNext) {
        this.changeImage(this.imagePages.next);
      }
    };

    let fileUploadInput = document.getElementById("file-upload");

    fileUploadInput.onchange = () => {
      this.displayImages(fileUploadInput);
    };
  }

  displayImages(input) {
    if (input.files && input.files[0]) {
      // this.images = new Pagination(input.files);
      let imageElements = [];

      // Promises array
      let promises = [];

      // Read all the files
      for (let file of input.files) {
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
        this.imagePages = new Pagination(imageElements);
        this.changeImage(this.imagePages.current);
      });
    }
  }

  changeImage(image) {
    document.getElementById("preview-image").replaceChildren(image);
    document.getElementById("image-count").innerText =
      this.imagePages.currentPage + 1;
  }

  switchSlide(slide) {
    this.hideOtherSlides(slide.dataset.slideName);
    this.updateSlideControls();
  }

  hideOtherSlides(slideName) {
    for (let element of document.getElementsByClassName("uploader-panel")) {
      if (element.dataset.slideName != slideName) {
        element.style.display = "none";
      } else {
        element.style.display = "flex";
      }
    }
  }

  updateSlideControls() {
    let rightButton = document.getElementById("right-button");
    let leftButton = document.getElementById("left-button");
    let uploadButton = document.getElementById("upload-button");

    document.getElementById("uploader-title-text").innerText =
      this.uploaderSlides.current.dataset.slideTitle;
    if (this.uploaderSlides.hasNext && this.uploaderSlides.hasPrev) {
      // has next and prev
      leftButton.style.visibility = "visible";
      rightButton.style.visibility = "visible";
      rightButton.style.display = "block";
      uploadButton.style.display = "none";
    } else if (!this.uploaderSlides.hasNext && this.uploaderSlides.hasPrev) {
      // Has no next but has prev
      leftButton.style.visibility = "visible";
      rightButton.style.visibility = "hidden";
      rightButton.style.display = "none";
      uploadButton.style.display = "block";
    } else if (this.uploaderSlides.hasNext && !this.uploaderSlides.hasPrev) {
      // has next but no prev
      leftButton.style.visibility = "hidden";
      rightButton.style.visibility = "visible";
      rightButton.style.display = "block";
      uploadButton.style.display = "none";
    }
  }

  invokeForm() {
    let uploaderForm = document.getElementById("uploader-form");
    let fileInput = document.getElementById("file-upload");

    if (fileInput.files.length === 0) {
      alert("Please select some files!");
    } else {
      uploaderForm.submit();
    }
  }
}

// function slide1() {
//   // Update the title
//   document.getElementById("uploader-title-text").innerText = "Select Files";

//   // update the buttons
//   document.getElementById("left-button").style.visibility = "hidden";
//   document.getElementById("right-button").style.visibility = "visible";
//   document.getElementById("right-button").onclick = () => {
//     slide2();
//   };
//   document.getElementById("upload-button").style.display = "none";
//   document.getElementById("right-button").style.display = "block";
//   // Make all other slides invisible
//   hideOtherSlides("first-panel");
// }

// function slide2() {
//   // Update the title
//   document.getElementById("uploader-title-text").innerText = "Select Tags";

//   // update the buttons
//   document.getElementById("left-button").style.visibility = "visible";
//   document.getElementById("left-button").onclick = () => {
//     slide1();
//   };
//   document.getElementById("right-button").style.visibility = "visible";
//   document.getElementById("right-button").onclick = () => {
//     slide3();
//   };
//   document.getElementById("right-button").style.display = "block";
//   document.getElementById("upload-button").style.display = "none";
//   // Make all other slides invisible
//   hideOtherSlides("second-panel");
// }

// function slide3() {
//   // Update the title
//   document.getElementById("uploader-title-text").innerText =
//     "Extra Information";

//   // update the buttons
//   document.getElementById("left-button").style.visibility = "visible";
//   document.getElementById("left-button").onclick = () => {
//     slide2();
//   };
//   document.getElementById("right-button").style.display = "none";
//   document.getElementById("upload-button").style.display = "block";

//   // Make all other slides invisible
//   hideOtherSlides("third-panel");
// }

export { PostUpload };
