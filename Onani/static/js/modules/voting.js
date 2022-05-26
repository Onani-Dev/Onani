/**
 * @Author: kapsikkum
 * @Date:   2022-04-24 01:29:16
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-05-26 15:26:29
 */

class PostVoting {
  constructor() {
    this.upvoteButton = document.getElementById("upvote-button");
    this.downvoteButton = document.getElementById("downvote-button");
    this.scoreCount = document.getElementById("post-score-count");
    this.postID = document.getElementById("content-container").dataset.postId;

    this.upvoteButton.onclick = () => {
      this.addUpvote();
    };

    this.downvoteButton.onclick = () => {
      this.addDownvote();
    };
  }

  sendVote(type) {
    let settings = {
      url: "/api/v1/posts/vote",
      method: "POST",
      data: JSON.stringify({ post_id: this.postID, type: type }),
      headers: {
        "Content-Type": "application/json",
      },
    };

    $.ajax(settings).done((response) => {
      this.updateButtons(response);
    });
  }

  addUpvote() {
    if (this.upvoteButton.classList.contains("disabled")) {
      return;
    }
    this.upvoteButton.classList.add("disabled");
    this.downvoteButton.classList.add("disabled");

    this.sendVote("upvote");
  }

  addDownvote() {
    if (this.downvoteButton.classList.contains("disabled")) {
      return;
    }
    this.upvoteButton.classList.add("disabled");
    this.downvoteButton.classList.add("disabled");

    this.sendVote("downvote");
  }

  updateButtons(apiData) {
    // Change the score count
    this.scoreCount.innerText = apiData.score;

    // Change the colour of the score count
    if (apiData.score > 0) {
      this.scoreCount.className = "positive";
    } else if (apiData.score < 0) {
      this.scoreCount.className = "negative";
    } else {
      this.scoreCount.className = "neutral";
    }

    // Change the button states
    if (apiData.has_downvoted) {
      this.downvoteButton.classList.add("voted");
      this.upvoteButton.classList.remove("voted");
    } else if (apiData.has_upvoted) {
      this.upvoteButton.classList.add("voted");
      this.downvoteButton.classList.remove("voted");
    } else if (!apiData.has_downvoted && !apiData.has_upvoted) {
      this.upvoteButton.classList.remove("voted");
      this.downvoteButton.classList.remove("voted");
    }

    this.upvoteButton.classList.remove("disabled");
    this.downvoteButton.classList.remove("disabled");
  }
}

export { PostVoting };
