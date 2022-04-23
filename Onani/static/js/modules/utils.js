/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 12:55:15
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-22 04:07:23
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

// Escape route
const escapeButton = (e) => {
  if (e.key === "Escape") {
    document.body.innerHTML = "";
    location.href = "https://taiko.bui.pm/";
  }
};

// Text copy function
const copyText = (text) => {
  navigator.clipboard.writeText(text).then(
    function () {
      alert("Copied to clipboard!");
    },
    function () {
      alert("Failed to copy.");
    }
  );
};

export { Pagination, escapeButton, copyText };
