/**
 * @Author: kapsikkum
 * @Date:   2022-06-16 11:47:19
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-06-19 15:17:29
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
    this.editCancelButton = document.getElementById("post-edit-box-cancel");

    // Elements to hide/unhide
    this.commentsBox = document.getElementById("comments-box");
    this.infoBox = document.getElementById("info-box");
    this.editorBox = document.getElementById("edit-box");

    // Save button
    this.saveButton = document.getElementById("post-edit-box-save");

    // Input values
    this.parentIdInput = document.getElementById("post-edit-parent");
    this.postRatingInput = document.getElementById("post-edit-rating");
    this.postSourceInput = document.getElementById("post-edit-source");
    this.postDescription = document.getElementById("post-edit-desc");
    this.postTags = document.getElementById("post-edit-tags");
    this.postOldTags = document.getElementById("post-edit-old-tags");

    // button onclick event
    this.editButton.onclick = () => {
      this.toggleEditMode();
    };

    this.editCancelButton.onclick = () => {
      this.toggleEditMode();
    };

    this.saveButton.onclick = () => {
      this.saveEdits();
    };
  }
  /**
   * Toggle the edit mode (makes info and comments invisible and shows editing box)
   */
  toggleEditMode() {
    // Toggle the comment box
    this.commentsBox.style.display =
      this.commentsBox.style.display == "none" ? "block" : "none";

    // Toggle the information box
    this.infoBox.style.display =
      this.infoBox.style.display == "none" ? "block" : "none";

    // Toggle the information box
    this.editorBox.style.display =
      this.editorBox.style.display == "flex" ? "none" : "flex";

    // Toggle the text on the Button
    this.editButton.innerText =
      this.editButton.innerText == "Edit Post" ? "Exit Edit Mode" : "Edit Post";
  }

  saveEdits() {
    let settings = {
      url: "/api/v1/post",
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      data: JSON.stringify({
        id: this.postID,
        description: this.postDescription.value,
        tags: this.postTags.value,
        old_tags: this.postOldTags.value,
        rating: this.postRatingInput.value,
        source: this.postSourceInput.value,
      }),
    };

    $.ajax(settings).done(function (response) {
      location.reload();
    });
  }
}

export { PostEditor };
