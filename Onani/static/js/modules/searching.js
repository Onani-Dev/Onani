/**
 * @Author: kapsikkum
 * @Date:   2022-04-21 03:27:58
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-23 02:47:24
 */

class PostsSearch {
  constructor() {
    // Searchbox enter event
    document.getElementById("search-input").onkeyup = (e) => {
      if (e.key === "Enter") {
        this.searchPosts();
      }
    };

    // Search icon click event
    document.getElementById("search-icon").onclick = () => {
      this.searchPosts();
    };
  }

  searchPosts() {
    let searchBox = document.getElementById("search-input");
    if (searchBox.value) {
      let windowParams = new URLSearchParams();
      windowParams.set("tags", searchBox.value);
      location.href = `/posts/?${windowParams.toString()}`;
    }
  }
}

export { PostsSearch };
