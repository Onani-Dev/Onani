/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 12:55:15
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-06-19 13:38:02
 */

/**
 * Pagination for an array
 */
class Pagination {
  /**
   *
   * @param {Array} items
   */
  constructor(items) {
    this.items = items;
    this.currentPage = 0;
  }

  /**
   * Max length of the items array
   */
  get maxLength() {
    return this.items.length - 1;
  }

  /**
   * Check if the array has a previous element
   */
  get hasPrev() {
    if (this.currentPage > 0) {
      return true;
    }
    return false;
  }

  /**
   * Check if the array has a next element
   */
  get hasNext() {
    if (this.currentPage < this.maxLength) {
      return true;
    }
    return false;
  }

  /**
   *
   * @returns The current page's object
   */
  get current() {
    return this.items[this.currentPage];
  }

  /**
   * Changes the currentPage to the next one, and returns it.
   * @returns The next page's object.
   */
  get next() {
    if (!this.hasNext) {
      throw new RangeError("No next page available");
    }
    this.currentPage += 1;
    return this.items[this.currentPage];
  }

  /**
   * Changes the currentPage to the previous one, and returns it.
   * @returns The previous page's object.
   */
  get prev() {
    if (!this.hasPrev) {
      throw new RangeError("No previous page available");
    }
    this.currentPage -= 1;
    return this.items[this.currentPage];
  }

  /**
   * Peeks the next object in pagination without changing the current.
   * @returns The next page's object.
   */
  get peekNext() {
    if (!this.hasNext) {
      return null;
    }
    return this.items[this.currentPage + 1];
  }

  /**
   * Peeks the previous object in pagination without changing the current.
   * @returns The previous page's object.
   */
  get peekPrev() {
    if (!this.hasPrev) {
      return null;
    }
    return this.items[this.currentPage - 1];
  }
}

class Alerter {
  constructor() {
    this.alertContainer = document.getElementById("alert-container");
  }

  _addAlert(text, type, timed) {
    // Create the alert div
    let alert = document.createElement("div");

    // Add the class name to the alert
    alert.className = "alert";

    // Create the close button
    let closeButton = document.createElement("span");

    // Add the class name to the close button
    closeButton.className = "close-button";

    // Make the close button with the &times; character
    closeButton.innerHTML = "&times;";

    // When someone clicks on a close button
    closeButton.onclick = function () {
      let div = this.parentElement;
      div.style.opacity = "0";
      setTimeout(() => {
        div.style.display = "none";
      }, 100);
    };

    // Add the type of alert to the alert
    alert.classList.add(type);

    // Add the text to the alert
    alert.innerText = text;

    // Add the close button to the alert
    alert.appendChild(closeButton);

    // add the alert to the top of the container
    this.alertContainer.prepend(alert);

    // Delete after a while if it is set to timed
    if (timed) {
      setTimeout(() => {
        alert.parentElement.removeChild(alert);
      }, 10000);
    }
  }

  message(text, timed = false) {
    this._addAlert(text, "message", timed);
  }

  success(text, timed = false) {
    this._addAlert(text, "success", timed);
  }

  warning(text, timed = false) {
    this._addAlert(text, "warning", timed);
  }

  error(text, timed = false) {
    this._addAlert(text, "error", timed);
  }
}

// Escape route
const escapeButton = (e) => {
  if (e.key === "Escape") {
    document.body.innerHTML = "";
    location.href = "https://taiko.bui.pm/";
  }
};

// Text copy function
const copyText = (text) => {
  let alerter = new Alerter();
  navigator.clipboard.writeText(text).then(
    function () {
      alerter.success("Copied to clipboard!", true);
    },
    function () {
      alerter.error("Failed to copy.", true);
    }
  );
};

export { Pagination, escapeButton, copyText, Alerter };
