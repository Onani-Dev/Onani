/*
 * @Author: Blakeando
 * @Date:   2020-09-14 22:24:47
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-15 17:13:48
 */
'use strict';
const tabcontent = document.getElementsByClassName("profile-tab-content");
const tablinks = document.getElementsByClassName("profile-tab-link");
const windowHash = window.location.hash.replace("#", "");
if (window.location.hash != "" && ["bio", "settings", "posts"].includes(windowHash)) {
  document.getElementById(window.location.hash.replace("#", "")).click();
}
else {
  console.log("clicking default")
  document.getElementById("bio").click();
}

function changeTab(evt, tabName) {
  for (var i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
} 