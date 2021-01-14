/*
 * @Author: kapsikkum
 * @Date:   2020-10-13 17:15:13
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2020-11-01 17:24:02
 */
'use strict';

const searchBox = document.getElementById("search-input"),
    postsPageUrl = new URL(`${window.location.protocol}//${window.location.host}/posts/`);

searchBox.onkeyup = function (e) {
    if (e.key == "Enter") {
        let windowParams = new URLSearchParams();
        windowParams.set("tags", searchBox.value);
        postsPageUrl.search = windowParams.toString();
        location.href = postsPageUrl.href;
    }
}
