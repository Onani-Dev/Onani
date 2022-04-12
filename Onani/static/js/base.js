/**
 * @Author: kapsikkum
 * @Date:   2022-03-28 22:16:17
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-12 18:40:49
 */

const dateFormatElements = document.getElementsByClassName("date-format"),
  markdownFormatElements = document.getElementsByClassName("markdown-format"),
  twemojiFormatElements = document.getElementsByClassName("twemoji-format");

for (let element of dateFormatElements) {
  try {
    element.innerHTML = luxon.DateTime.fromISO(element.innerHTML).toFormat(
      "fff"
    );
  } catch (e) {
    console.error(e);
  }
}

for (let element of markdownFormatElements) {
  let converter = new showdown.Converter();
  try {
    element.innerHTML = converter.makeHtml(element.innerHTML);
  } catch (e) {
    console.error(e);
  }
}

for (let element of twemojiFormatElements) {
  try {
    twemoji.parse(element);
  } catch (e) {
    console.error(e);
  }
}

document.onkeyup = function (e) {
  if (e.key == "Escape") {
    document.body.innerHTML = "";
    location.href = "https://taiko.bui.pm/";
  }
};

function openNav() {
  document.getElementById("side-navigation").style.width = "250px";
}

function closeNav() {
  document.getElementById("side-navigation").style.width = "0";
}
