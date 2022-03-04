/**
 * @Author: kapsikkum
 * @Date:   2022-03-05 02:50:35
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-03-05 03:20:12
 */
'use strict';
const newsContainer = document.getElementById("news-container");

fetch("/api/news", {method: 'GET'})
.then(response => {
    response.json().then(json => {
        json.forEach(element => {
            var newsPost = document.createElement("li"),
                newsLink = document.createElement("a");
            newsLink.href = `/news/${element.id}`;
            newsLink.innerText = element.title;
            newsPost.appendChild(newsLink);
            newsContainer.appendChild(newsPost);
        });
    });
  });

