/*
 * @Author: kapsikkum
 * @Date:   2020-09-14 22:24:47
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-03-11 00:00:54
 */
'use strict';
const tabcontent = document.getElementsByClassName("profile-tab-content"),
  tablinks = document.getElementsByClassName("profile-tab-link"),
  settingsTabContent = document.getElementsByClassName("settings-tab-content"),
  settingsTabLinks = document.getElementsByClassName("settings-tab-link");
// const pageURL = new URL(window.location.href);
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


function changeSettingsTab(evt, tabName) {
  for (var i = 0; i < settingsTabContent.length; i++) {
    settingsTabContent[i].style.display = "none";
  }

  for (i = 0; i < settingsTabLinks.length; i++) {
    settingsTabLinks[i].className = settingsTabLinks[i].className.replace(" active", "");
  }

  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

function CopyText(text) {
  const listener = function (ev) {
    ev.preventDefault();
    ev.clipboardData.setData('text/html', text);
    ev.clipboardData.setData('text/plain', text);
  };
  document.addEventListener('copy', listener);
  document.execCommand('copy');
  document.removeEventListener('copy', listener);
  alert("Copied to clipboard!");
}

try {
  document.getElementById("account-settings").click();
} catch (error) {}