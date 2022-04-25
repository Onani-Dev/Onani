/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 12:27:55
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-25 17:11:32
 */
// import { DateTime } from "./external/luxon.min.js";
// import { Converter } from "./external/showdown.min.js";
// import { parse as twemojiParse } from "./external/twemoji.min.js";

/**
 * Element Formatter for formatting html elements with classes.
 */
class ElementFormatter {
  /**
   * Regex for the Onani emotes.
   */
  get customEmotes() {
    return /(:don:|:katsu:|:desuwa:|:dirt:|:armagan:)/g;
  }

  /**
   * Emote table for Onani emotes.
   */
  get emojiTable() {
    return {
      don: "/static/svg/don.svg",
      katsu: "/static/svg/katsu.svg",
      desuwa: "/static/svg/desuwa.svg",
      dirt: "/static/image/dirt_small.gif",
      armagan: "/static/image/armagan_small.gif",
    };
  }

  /**
   * Format all elements.
   */
  formatAll() {
    this.dateFormat();
    this.markdownFormat();
    this.twemojiFormat();
    this.emoteFormat();
  }

  /**
   * Format all date-format elements with human readable time from luxon
   */
  dateFormat() {
    for (let element of document.getElementsByClassName("date-format")) {
      try {
        let date = luxon.DateTime.fromISO(element.innerHTML);
        element.innerHTML = date.toFormat("fff");
        if (element.classList.contains("human-time")) {
          element.innerHTML += ` (${date.toRelativeCalendar()})`;
        }
      } catch (e) {
        console.error(e);
      }
    }
  }

  /**
   * Format all markdown-format elements
   */
  markdownFormat() {
    for (let element of document.getElementsByClassName("markdown-format")) {
      let converter = new showdown.Converter();
      try {
        element.innerHTML = converter.makeHtml(element.innerHTML);
      } catch (e) {
        console.error(e);
      }
    }
  }

  /**
   * Format all twemoji-format elements
   */
  twemojiFormat() {
    for (let element of document.getElementsByClassName("twemoji-format")) {
      try {
        twemoji.parse(element);
      } catch (e) {
        console.error(e);
      }
    }
  }

  /**
   * Format all emote-format elements
   */
  emoteFormat() {
    for (let element of document.getElementsByClassName("emote-format")) {
      try {
        element.innerHTML = element.innerHTML.replace(
          this.customEmotes,
          (current) => {
            let emote = document.createElement("img");
            emote.src = this.emojiTable[current.replace(/:/g, "")];
            emote.className = "emoji";
            emote.draggable = false;
            emote.alt = current;
            return emote.outerHTML;
          }
        );
      } catch (e) {
        console.error(e);
      }
    }
  }
}

export { ElementFormatter };
