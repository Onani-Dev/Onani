/**
 * @Author: kapsikkum
 * @Date:   2022-04-04 01:58:23
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-04 04:05:08
 */
const commentTextInput = document.getElementById("post-comment-input"),
  commentContainer = document.getElementById("comment-container"),
  postButton = document.getElementById("post-comment-submit");

function contructCommentElement(comment) {
  let userProfileContainer = document.createElement("div"),
    commentPostContainer = document.createElement("div"),
    userProfilePicture = document.createElement("img"),
    userName = document.createElement("a"),
    commentContent = document.createElement("p");

  commentPostContainer.className = "comment-post";
  userProfilePicture.src = comment.author.settings.avatar;
  userName.href = `/users/${comment.author.id}`;
  userName.innerText = comment.author.username;
  commentContent.innerHTML = comment.content;

  userProfileContainer.className = "comment-post-profile";
  userProfileContainer.appendChild(userProfilePicture);
  userProfileContainer.appendChild(userName);

  commentPostContainer.appendChild(userProfileContainer);
  commentPostContainer.appendChild(commentContent);

  return commentPostContainer;
}

function loadComments() {
  "use strict";
  var settings = {
    url: "/api/comments",
    method: "GET",
    data: { post_id: postID },
  };

  $.ajax(settings).done(function (response) {
    commentContainer.innerHTML = "";
    if (response.data.length == 0) {
      noCom = document.createElement("h2");
      noCom.innerText = "No Comments on this post.";
      commentContainer.appendChild(noCom);
    }
    response.data.forEach((comment) => {
      commentContainer.appendChild(contructCommentElement(comment));
    });
  });
}

function postComment() {
  "use strict";
  if (commentTextInput.value) {
    var settings = {
      url: "/api/comments/post",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      data: JSON.stringify({
        post_id: postID,
        content: commentTextInput.value,
      }),
    };

    $.ajax(settings).done(function (response) {
      $(commentContainer).prepend(contructCommentElement(response));
      commentTextInput.value = "";
    });
  }
}

loadComments();
commentTextInput.onkeyup = function (e) {
  "use strict";
  if (e.key == "Enter") {
    postComment();
  }
};

postButton.onclick = function (e) {
  postComment();
};
