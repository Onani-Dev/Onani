/**
 * @Author: kapsikkum
 * @Date:   2022-04-04 01:58:23
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-05-14 14:00:04
 */

// import { ajax } from "jquery";
// import { DateTime } from "./external/luxon.min.js";
// import { parse as twemojiParse } from "./external/twemoji.min.js";

const constructCommentElement = (comment) => {
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
};

class PostCommenter {
  constructor() {
    // Values
    this.next = null;
    this.prev = null;
    this.total = 0;

    // Post ID
    this.postID = document.getElementById("content-container").dataset.postId;

    // Comment container element
    this.commentContainer = document.getElementById("comment-container");

    // Comment text input
    this.commentTextInput = document.getElementById("post-comment-input");

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
  }

  editValues() {}

  /**
   * Load the comments into the search box
   */
  loadComments() {
    let settings = {
      url: "/api/v1/comments",
      method: "GET",
      data: { post_id: this.postID },
    };

    $.ajax(settings).done((response) => {
      this.commentContainer.replaceChildren();
      if (response.data.length === 0) {
        let noCom = document.createElement("h2");
        noCom.id = "no-comments-message";
        noCom.classList.add("system-text");
        noCom.innerHTML = "No Comments on this post.";
        this.commentContainer.appendChild(noCom);
      }
      response.data.forEach((comment) => {
        this.commentContainer.appendChild(constructCommentElement(comment));
      });
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
      $.ajax(settings).done((response) => {
        let noCommentsMessage = document.getElementById("no-comments-message");
        if (noCommentsMessage) {
          noCommentsMessage.parentNode.removeChild(noCommentsMessage);
        }
        this.loadComments();
      });
    }
  }
}

export { PostCommenter };
