/*
 * @Author: Blakeando
 * @Date:   2020-09-14 22:24:47
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-17 21:37:53
 */
'use strict';
const tabcontent = document.getElementsByClassName("profile-tab-content");
const tablinks = document.getElementsByClassName("profile-tab-link");
const pageURL = new URL(window.location.href);
const windowParams = new URLSearchParams(window.location.search);
if (windowParams.get("t") != "" && ["bio", "settings", "posts"].includes(windowParams.get("t"))) {
  document.getElementById(windowParams.get("t")).click();
}
else {
  document.getElementById("bio").click();
}

function changeTab(evt, tabName) {
  windowParams.set("t", tabName.replace("-tab", ""));
  pageURL.search = windowParams.toString();
  window.history.replaceState({ path: pageURL.href }, '', pageURL.href);

  for (var i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
} 