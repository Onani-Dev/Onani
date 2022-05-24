/**
 * @Author: kapsikkum
 * @Date:   2022-04-21 18:33:12
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-05-24 09:16:39
 */
import {
  ElementFormatter,
  PostsSearch,
  SideNavbarControls,
} from "./modules/index.min.js";

// Formatter
let formatter = new ElementFormatter();
formatter.formatAll();

// Search box
let search = new PostsSearch();

// Mobile sidenav
let sideNav = new SideNavbarControls();

document.addEventListener("DOMContentLoaded", function (event) {
  for (let img of document.querySelectorAll("img")) {
    img.onerror = function () {
      this.src = "/static/image/missing_file.png";
      this.title = "An error has occurred while loading this image.";
    };
    img.src = img.src;
  }
});
