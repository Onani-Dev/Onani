/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 15:17:46
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-19 15:25:36
 */
import { parse as twemojiParse } from "twemoji";
import { DateTime } from "luxon";

const newsContainer = document.getElementById("news-container");

fetch("/api/news", { method: "GET" }).then((response) => {
  response.json().then((json) => {
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
      newsContainer.appendChild(newsPost);
    });
  });
});
