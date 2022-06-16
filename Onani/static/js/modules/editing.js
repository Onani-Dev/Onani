/**
 * @Author: kapsikkum
 * @Date:   2022-06-16 11:47:19
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-06-16 14:01:25
 */

import { Alerter } from "./index.min.js";

class PostEditor {
  constructor() {
    // Alerter
    this.alerter = new Alerter();

    // Post ID
    this.postID = document.getElementById("content-container").dataset.postId;

    // Editing button
    this.editButton = document.getElementById("edit-mode-button");

    // Elements to hide/unhide
    this.commentsBox = document.getElementById("comments-box");
    this.infoBox = document.getElementById("info-box");
    this.editorBox = document.getElementById("edit-box");

    // button onclick event
    this.editButton.onclick = () => {
      this.toggleEditMode();
    };
  }

  toggleEditMode() {
    // Toggle the comment box
    this.commentsBox.style.display =
      this.commentsBox.style.display == "none" ? "block" : "none";

    // Toggle the information box
    this.infoBox.style.display =
      this.infoBox.style.display == "none" ? "block" : "none";

    // Toggle the information box
    this.editorBox.style.display =
      this.editorBox.style.display == "block" ? "none" : "block";

    // Toggle the text on the Button
    this.editButton.innerText =
      this.editButton.innerText == "Edit Post" ? "Exit Edit Mode" : "Edit Post";
  }
}

export { PostEditor };
