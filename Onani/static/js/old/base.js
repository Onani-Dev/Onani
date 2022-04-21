/**
 * @Author: kapsikkum
 * @Date:   2022-03-28 22:16:17
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-21 21:39:15
 */

// Format all date-format elements
for (let element of document.getElementsByClassName("date-format")) {
  try {
    element.innerHTML = luxon.DateTime.fromISO(element.innerHTML).toFormat(
      "fff"
    );
  } catch (e) {
    console.error(e);
  }
}

// Format all markdown-format elements
for (let element of document.getElementsByClassName("markdown-format")) {
  let converter = new showdown.Converter();
  try {
    element.innerHTML = converter.makeHtml(element.innerHTML);
  } catch (e) {
    console.error(e);
  }
}

// Format all twemoji-format elements
for (let element of document.getElementsByClassName("twemoji-format")) {
  try {
    twemoji.parse(element);
  } catch (e) {
    console.error(e);
  }
}

// Escape route
document.onkeyup = function (e) {
  if (e.key === "Escape") {
    document.body.innerHTML = "";
    location.href = "https://taiko.bui.pm/";
  }
};

// Opening navigation
function openNav() {
  document.getElementById("side-navigation").style.width = "250px";
}

// Closing navigation
function closeNav() {
  document.getElementById("side-navigation").style.width = "0";
}

// Text copy function
function copyText(text) {
  navigator.clipboard.writeText(text).then(
    function () {
      alert("Copied to clipboard!");
    },
    function () {
      alert("Failed to copy.");
    }
  );
}
