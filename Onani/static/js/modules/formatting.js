/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 12:27:55
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-19 12:52:12
 */
import { DateTime } from "luxon";
import { Converter } from "showdown";

// Format all date-format elements
(() => {
  for (let element of document.getElementsByClassName("date-format")) {
    try {
      element.innerHTML = DateTime.fromISO(element.innerHTML).toFormat("fff");
    } catch (e) {
      console.error(e);
    }
  }
})();

// Format all markdown-format elements
(() => {
  for (let element of document.getElementsByClassName("markdown-format")) {
    let converter = new Converter();
    try {
      element.innerHTML = converter.makeHtml(element.innerHTML);
    } catch (e) {
      console.error(e);
    }
  }
})();

// Format all twemoji-format elements
(() => {
  for (let element of document.getElementsByClassName("twemoji-format")) {
    try {
      twemoji.parse(element);
    } catch (e) {
      console.error(e);
    }
  }
})();
