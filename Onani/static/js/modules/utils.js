/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 12:55:15
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-19 13:11:10
 */

// Escape route
const escapeButton = (e) => {
  if (e.key == "Escape") {
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

export { escapeButton, copyText };
