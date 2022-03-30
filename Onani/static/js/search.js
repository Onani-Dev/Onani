/*
 * @Author: kapsikkum
 * @Date:   2020-10-13 17:15:13
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-03-30 18:14:07
 */
const searchBox = document.getElementById("search-input");

function searchPosts() {
  "use strict";
  if (searchBox.value) {
    let windowParams = new URLSearchParams();
    windowParams.set("tags", searchBox.value);
    location.href = `/posts/?${windowParams.toString()}`;
  }
}

searchBox.onkeyup = function (e) {
  "use strict";
  if (e.key == "Enter") {
    searchPosts();
  }
};
