/**
 * @Author: kapsikkum
 * @Date:   2022-03-19 14:50:20
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-20 23:28:39
 */
const tagContainer = document.getElementById("tag-container");

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
        tagListItem.onclick = function (e) {
          location.href = `/posts/?tags=${tag.name}`;
        };
        tagContainer.appendChild(tagListItem);
      }
    });
  });
});
