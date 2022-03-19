/*
 * @Author: kapsikkum
 * @Date:   2020-10-13 17:15:13
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-03-19 14:56:59
 */
"use strict";

const searchBox = document.getElementById("search-input");
const pageURL = new URL(window.location.href);

searchBox.onkeyup = function (e) {
  if (e.key == "Enter") {
    let windowParams = new URLSearchParams();
    windowParams.set("tags", searchBox.value);
    pageURL.search = windowParams.toString();
    location.href = pageURL.href;
  }
};
