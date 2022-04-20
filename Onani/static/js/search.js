/*
 * @Author: kapsikkum
 * @Date:   2020-10-13 17:15:13
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-21 00:14:33
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
