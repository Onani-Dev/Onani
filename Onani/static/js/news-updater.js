/**
 * @Author: kapsikkum
 * @Date:   2022-03-05 02:50:35
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-03-20 19:45:56
 */
const newsContainer = document.getElementById("news-container");

fetch("/api/news", { method: "GET" }).then((response) => {
  response.json().then((json) => {
    json.data.forEach((news) => {
      var newsPost = document.createElement("li"),
        newsLink = document.createElement("a"),
        newsTime = document.createElement("h6");
      newsLink.href = `/news/${news.id}`;
      newsLink.innerText = news.title;
      newsTime.textContent = `(${moment.utc(news.created_at).fromNow()})`;
      twemoji.parse(newsLink);
      newsPost.appendChild(newsLink);
      newsPost.appendChild(newsTime);
      newsContainer.appendChild(newsPost);
    });
  });
});
