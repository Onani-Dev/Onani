/**
 * @Author: kapsikkum
 * @Date:   2022-04-21 03:27:58
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-21 03:30:39
 */

class PostsSearch {
  constructor() {
    this.searchBox = document.getElementById("search-input");

    this.searchBox.onkeyup = function (e) {
      if (e.key == "Enter") {
        this.searchPosts();
      }
    };
  }

  searchPosts() {
    if (this.searchBox.value) {
      let windowParams = new URLSearchParams();
      windowParams.set("tags", this.searchBox.value);
      location.href = `/posts/?${windowParams.toString()}`;
    }
  }
}

export { PostsSearch };
