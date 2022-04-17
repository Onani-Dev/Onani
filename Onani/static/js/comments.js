/**
 * @Author: kapsikkum
 * @Date:   2022-04-04 01:58:23
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-17 10:16:52
 */
const commentTextInput = document.getElementById("post-comment-input"),
  commentContainer = document.getElementById("comment-container"),
  postButton = document.getElementById("post-comment-submit");

function contructCommentElement(comment) {
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

  userProfilePicture.onclick = function (e) {
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
  commentTime.innerHTML = `${luxon.DateTime.fromISO(
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

function loadComments() {
  "use strict";
  var settings = {
    url: "/api/comments",
    method: "GET",
    data: { post_id: postID },
  };

  $.ajax(settings).done(function (response) {
    commentContainer.innerHTML = "";
    if (response.data.length === 0) {
      let noCom = document.createElement("h2");
      noCom.id = "no-comments-message";
      noCom.classList.add("system-text");
      noCom.innerHTML = "No Comments on this post.";
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
      let noCommentsMessage = document.getElementById("no-comments-message");
      if (noCommentsMessage) {
        noCommentsMessage.parentNode.removeChild(noCommentsMessage);
      }
      $(commentContainer).prepend(contructCommentElement(response));
      commentTextInput.value = "";
    });
  }
}

loadComments();
// commentTextInput.onkeyup = function (e) {
//   "use strict";
//   if (e.key == "Enter") {
//     postComment();
//   }
// };

postButton.onclick = function (e) {
  postComment();
};
