/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 15:17:46
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-07-31 13:03:51
 */
// import { parse as twemojiParse } from "./external/twemoji.min.js";
// import { DateTime } from "./external/luxon.min.js";

class NewsBoxUpdater {
  /**
   * @Mattlau04 cry about it
   * @kero3009destiny laugh about it
   * @kapsikkum troll about it
   * @param {integer} milliseconds
   */
  constructor(milliseconds = 300000) {
    this.getNews();
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
    fetch("/api/v1/news", { method: "GET" }).then((response) => {
      response.json().then((json) => {
        // Clear news box and replace with new children
        newsContainer.replaceChildren();

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
          newsTime.textContent = `(${luxon.DateTime.fromISO(
            news.created_at
          ).toRelativeCalendar()})`;

          // make it twemoji
          twemoji.parse(newsLink);

          // append items
          newsPost.appendChild(newsLink);
          newsPost.appendChild(newsTime);

          // Add to news to add to element
          newsContainer.appendChild(newsPost);
        });
      });
    });
  }
}

class TagsBoxUpdater {
  constructor() {
    if (!sessionStorage.getItem("tagsCache")) {
      console.log("No cache");
      let tagsCache = JSON.stringify({
        cacheExpires: luxon.DateTime.now().toObject(),
        data: [],
      });
      sessionStorage.setItem("tagsCache", JSON.stringify(tagsCache));
    }

    this.displayTags();
  }

  constructTag(tag) {
    // Create the elements to add properties to
    let tagListItem = document.createElement("li"),
      tagText = document.createElement("p"),
      postCount = document.createElement("div");

    // The link of the tag
    tagText.href = `/posts/?tags=${tag.name}`;

    tagText.innerText = tag.humanized;

    // Add post count to div
    postCount.innerText = Humanize.compactInteger(tag.post_count, 1);

    // Add the classes
    tagListItem.classList.add(tag.type);

    // Add the elements to the page
    tagListItem.appendChild(tagText);
    tagListItem.appendChild(postCount);

    // The onclick event
    tagListItem.onclick = () => {
      location.href = `/posts/?tags=${tag.name}`;
    };

    // Hover title description thing
    tagListItem.title = tag.description;

    return tagListItem;
  }

  async fetchTags() {
    // let tagContainer = document.getElementById("tag-container");
    let tagElements = [];

    let apiURL = new URL(`${location.origin}/api/v1/tags`);
    apiURL.searchParams.append("sort", "post_count");
    apiURL.searchParams.append("order", "desc");

    const response = await fetch(apiURL);
    await response.json().then((json) => {
      json.data.forEach((tag) => {
        // Only show tag if it has more than 0 posts and isn't banned
        if (tag.post_count > 0 && tag.type != "banned") {
          tagElements.push(tag);
        }
      });
    });
    return tagElements;
  }

  async getTags() {
    let tagsCache = JSON.parse(sessionStorage.getItem("tagsCache"));
    if (
      luxon.DateTime.now() < luxon.DateTime.fromObject(tagsCache.cacheExpires)
    ) {
      return tagsCache.data;
    } else {
      sessionStorage.removeItem("tagsCache");
      let newData = await this.fetchTags();
      this.setTags(newData);
      return newData;
    }
  }

  setTags(data) {
    let tagsCache = {
      cacheExpires: luxon.DateTime.now().plus({ minutes: 10 }).toObject(),
      data: data,
    };
    sessionStorage.setItem("tagsCache", JSON.stringify(tagsCache));
  }

  displayTags() {
    let tagContainer = document.getElementById("tag-container");
    this.getTags().then((tags) => {
      tagContainer.replaceChildren();
      for (let tag of tags) {
        tagContainer.appendChild(this.constructTag(tag));
      }
    });
  }
}

export { NewsBoxUpdater, TagsBoxUpdater };
