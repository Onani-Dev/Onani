/**
 * @Author: kapsikkum
 * @Date:   2022-03-19 14:50:20
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-03-23 23:05:23
 */
const tagContainer = document.getElementById("tag-container");

fetch("/api/tags?sort=post_count&order=desc").then((response) => {
  response.json().then((json) => {
    json.data.forEach((tag) => {
      // Create the elements to add properties to
      var tagListItem = document.createElement("li"),
        tagLink = document.createElement("a"),
        postCount = document.createElement("div");

      // The link of the tag
      tagLink.href = `/posts/?tags=${tag.name}`;

      tagLink.innerText = tag.name;

      // Add post count to div
      postCount.innerText = tag.post_count;

      // Add the classes
      tagLink.classList.add("tag-list-item");
      tagListItem.classList.add(tag.type);

      // Add the elements to the page
      tagListItem.appendChild(tagLink);
      tagListItem.appendChild(postCount);
      tagContainer.appendChild(tagListItem);
    });
  });
});
