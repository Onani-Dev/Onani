/**
 * @Author: kapsikkum
 * @Date:   2022-03-19 14:50:20
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-03-20 21:00:54
 */
const tagContainer = document.getElementById("tag-container");

fetch("/api/tags?sort=post_count&order=desc").then((response) => {
  response.json().then((json) => {
    json.data.forEach((tag) => {
      // Create the elements to add properties to
      var tagListItem = document.createElement("li"),
        tagLink = document.createElement("a");

      // The link of the tag
      tagLink.href = `/posts/?tags=${tag.name}`;

      // Truncate the tag name if it's too long
      if (tag.name.length > 15) {
        tagLink.innerText = `${tag.name.slice(0, 15)}... ${tag.post_count}`;
      } else {
        tagLink.innerText = `${tag.name} ${tag.post_count}`;
      }

      // Add the classes
      tagLink.classList.add("tag-list-item");
      tagLink.classList.add(tag.type);

      // Add the elements to the page
      tagListItem.appendChild(tagLink);
      tagContainer.appendChild(tagListItem);
    });
  });
});
