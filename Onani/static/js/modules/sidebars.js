/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 15:17:46
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-21 03:34:32
 */
import { parse as twemojiParse } from "twemoji";
import { DateTime } from "luxon";

class NewsBoxUpdater {
  /**
   * @Mattlau04 cry about it
   * @kero3009destiny laugh about it
   * @kapsikkum troll about it
   * @param {integer} milliseconds
   */
  constructor(milliseconds = 300000) {
    setInterval(this.getNews, milliseconds);
  }

  /**
   * Fetch the news for the news box widget thing idk
   */
  getNews() {
    // TODO: Only update if news container is visible for mobile etc
    if (!document.hasFocus()) {
      // We don't need to update the news in the background
      return;
    }

    let newsContainer = document.getElementById("news-container");
    // Fetch new news from the api
    fetch("/api/news", { method: "GET" }).then((response) => {
      response.json().then((json) => {
        let news = [];
        json.data.forEach((news) => {
          // Make a list entry element
          let newsPost = document.createElement("li"),
            newsLink = document.createElement("a"),
            newsTime = document.createElement("h6");

          // Set the href
          newsLink.href = `/news/${news.id}`;

          // set the title
          newsLink.innerText = news.title;

          // set the content
          newsTime.textContent = `(${DateTime.fromISO(
            news.created_at
          ).toRelativeCalendar()})`;

          // make it twemoji
          twemojiParse(newsLink);

          // append items
          newsPost.appendChild(newsLink);
          newsPost.appendChild(newsTime);

          // Add to news to add to element
          news.push(newsPost);
        });

        // Clear news box and replace with new children
        newsContainer.replaceChildren(news);
      });
    });
  }
}

class TagsBoxUpdater {
  constructor() {
    this.getTags();
  }

  getTags() {
    let tagContainer = document.getElementById("tag-container");
    fetch("/api/tags?sort=post_count&order=desc").then((response) => {
      response.json().then((json) => {
        json.data.forEach((tag) => {
          // Only show tag if it has more than 0 posts and isn't banned
          if (tag.post_count > 0 && tag.type != "banned") {
            // Create the elements to add properties to
            var tagListItem = document.createElement("li"),
              tagLink = document.createElement("a"),
              postCount = document.createElement("div");

            // The link of the tag
            tagLink.href = `/posts/?tags=${tag.name}`;

            tagLink.innerText = tag.humanized;

            // Add post count to div
            postCount.innerText = tag.post_count;

            // Add the classes
            tagLink.classList.add("tag-list-item");
            tagListItem.classList.add(tag.type);

            // Add the elements to the page
            tagListItem.appendChild(tagLink);
            tagListItem.appendChild(postCount);
            tagListItem.onclick = () => {
              location.href = `/posts/?tags=${tag.name}`;
            };
            tagContainer.appendChild(tagListItem);
          }
        });
      });
    });
  }
}

export { NewsBoxUpdater, TagsBoxUpdater };
