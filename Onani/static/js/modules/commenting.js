/**
 * @Author: kapsikkum
 * @Date:   2022-04-04 01:58:23
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-05-18 14:09:24
 */

import { Alerter } from "./index.min.js";
// import { DateTime } from "./external/luxon.min.js";
// import { parse as twemojiParse } from "./external/twemoji.min.js";

class PostCommenter {
  constructor() {
    // Alerter
    this.alerter = new Alerter();

    // Values
    this.next = null;
    this.prev = null;
    this.total = 0;
    this.currentPage = 0;

    // Post ID
    this.postID = document.getElementById("content-container").dataset.postId;

    // Comment container element
    this.commentContainer = document.getElementById("comment-container");

    // Comment text input
    this.commentTextInput = document.getElementById("post-comment-input");

    // Comment header
    this.commentHeader = document.getElementById("comments-header");

    // Controls
    this.nextButton = document.getElementById("comments-control-right");
    this.prevButton = document.getElementById("comments-control-left");

    // Load the functions
    this.loadComments();

    // Comment input shift enter to send
    document.getElementById("post-comment-input").onkeydown = (e) => {
      if (e.key === "Enter" && e.shiftKey) {
        e.preventDefault();
        this.postComment();
      }
    };

    // Post button click to send
    document.getElementById("post-comment-submit").onclick = (e) => {
      this.postComment();
    };

    // Controls for the pages
    this.nextButton.onclick = () => {
      if (this.next) {
        this.currentPage = this.next;
        this.loadComments();
      }
    };
    this.prevButton.onclick = () => {
      if (this.prev) {
        this.currentPage = this.prev;
        this.loadComments();
      }
    };
  }

  /**
   * Construct an element from an api comment response
   * @param {*} comment
   * @returns HTMLDivElement
   */
  constructCommentElement(comment) {
    let userProfileContainer = document.createElement("div"),
      commentPostContainer = document.createElement("div"),
      userProfilePicture = document.createElement("img"),
      userName = document.createElement("a"),
      commentContent = document.createElement("p"),
      commentInfoContainer = document.createElement("div"),
      commentBody = document.createElement("div"),
      commentTime = document.createElement("div");

    // add the class to the post container
    commentPostContainer.className = "comment-post";

    // Add the properties to the profile picture
    userProfilePicture.src = comment.author.avatar_thumbnail;

    userProfilePicture.onclick = () => {
      location.href = `/users/${comment.author.id}`;
    };

    // Add the link to the user's profile
    userName.href = `/users/${comment.author.id}`;
    userName.innerText = comment.author.username;

    // add the comment content
    commentContent.innerHTML = comment.content;

    // Add class to the profile container
    userProfileContainer.className = "comment-post-profile";

    // Add the profile picture
    userProfileContainer.appendChild(userProfilePicture);

    // Use luxon to make human readable time
    commentTime.innerText = `${luxon.DateTime.fromISO(
      comment.created_at
    ).toFormat("fff")}`;

    // Add comment author username and time
    commentInfoContainer.appendChild(userName);
    commentInfoContainer.appendChild(commentTime);

    commentInfoContainer.className = "comment-post-info";

    commentBody.className = "comment-post-data";

    commentBody.appendChild(commentInfoContainer);

    commentBody.appendChild(twemoji.parse(commentContent));

    commentPostContainer.appendChild(userProfileContainer);
    commentPostContainer.appendChild(commentBody);

    return commentPostContainer;
  }

  updateControls() {
    // Modify the title with the total of comments
    this.commentHeader.innerText = `Comments (${this.total})`;

    if (this.next && this.prev) {
      // has next and prev
      this.prevButton.style.visibility = "visible";
      this.nextButton.style.visibility = "visible";
    } else if (!this.next && this.prev) {
      // Has no next but has prev
      this.prevButton.style.visibility = "visible";
      this.nextButton.style.visibility = "hidden";
    } else if (this.next && !this.prev) {
      // has next but no prev
      this.prevButton.style.visibility = "hidden";
      this.nextButton.style.visibility = "visible";
    }
  }

  /**
   * Load the comments into the search box
   */
  loadComments() {
    let settings = {
      url: "/api/v1/comments",
      method: "GET",
      data: { post_id: this.postID, page: this.currentPage },
    };

    $.ajax(settings).done((response) => {
      // Delete current elements iside container
      this.commentContainer.replaceChildren();

      // Check the length of the data
      if (response.data.length === 0) {
        // Add a message saying "No comments on this post." if there are no comments.
        let noCom = document.createElement("h2");
        noCom.id = "no-comments-message";
        noCom.classList.add("system-text");
        noCom.innerHTML = "No Comments on this post.";
        this.commentContainer.appendChild(noCom);
      }

      // Iterate through the data
      response.data.forEach((comment) => {
        // Append a constructed comment
        this.commentContainer.appendChild(
          this.constructCommentElement(comment)
        );
      });

      // Update the values to the new ones.
      this.total = response.total;
      this.next = response.next;
      this.prev = response.prev;

      // Update the controls.
      this.updateControls();
    });
  }

  /**
   * Post a comment on the current post to the server.
   */
  postComment() {
    if (this.commentTextInput.value) {
      let settings = {
        url: "/api/v1/comments",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        data: JSON.stringify({
          post_id: this.postID,
          content: this.commentTextInput.value,
        }),
      };
      this.commentTextInput.value = "";
      $.ajax(settings).always((response) => {
        if (response.status === 429) {
          this.alerter.error("You're commenting too fast! Slow down.", true);
        } else {
          this.loadComments();
        }
      });
    }
  }
}

export { PostCommenter };
