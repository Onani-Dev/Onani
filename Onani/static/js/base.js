/**
 * @Author: kapsikkum
 * @Date:   2022-03-28 22:16:17
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-09 01:38:28
 */

const dateFormatElements = document.getElementsByClassName("date-format");

for (let element of dateFormatElements) {
  try {
    element.innerHTML = luxon.DateTime.fromISO(element.innerHTML).toFormat(
      "fff"
    );
  } catch (e) {
    console.log(e);
  }
}

document.onkeyup = function (e) {
  if (e.keyCode == 27) {
    document.body.innerHTML = "";
    location.href = "https://en.wikipedia.org/wiki/Taiko_no_Tatsujin";
  }
};

function openNav() {
  document.getElementById("side-navigation").style.width = "250px";
  document.getElementById("main").style.marginRight = "250px";
}

function closeNav() {
  document.getElementById("side-navigation").style.width = "0";
  document.getElementById("main").style.marginRight = "0";
}
