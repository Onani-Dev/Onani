/**
 * @Author: kapsikkum
 * @Date:   2022-04-21 03:27:58
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-28 17:33:09
 */

class PostsSearch {
  constructor() {
    // Elements
    this.searchInput = document.getElementById("search-input");
    this.searchIcon = document.getElementById("search-icon");

    // Searchbox enter event
    this.searchInput.onkeyup = (e) => {
      if (e.key === "Enter") {
        this.searchPosts();
      }
    };

    // Search icon click event
    this.searchIcon.onclick = () => {
      this.searchPosts();
    };
  }

  searchPosts() {
    if (this.searchInput.value) {
      let windowParams = new URLSearchParams();
      windowParams.set("tags", this.searchInput.value);
      location.href = `/posts/?${windowParams.toString()}`;
    }
  }
}

export { PostsSearch };
