/**
 * @Author: kapsikkum
 * @Date:   2022-04-21 03:27:58
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-21 21:18:09
 */

class PostsSearch {
  constructor() {
    // Allow use of this inside the events
    let searchFunc = this.searchPosts;

    // Searchbox enter event
    document.getElementById("search-input").onkeyup = (e) => {
      if (e.key === "Enter") {
        searchFunc();
      }
    };

    // Search icon click event
    document.getElementById("search-icon").onkeyup = () => {
      searchFunc();
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
