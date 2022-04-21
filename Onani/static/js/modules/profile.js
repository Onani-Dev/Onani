/**
 * @Author: kapsikkum
 * @Date:   2022-04-20 23:44:57
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-22 01:33:26
 */
// import { Croppie } from "./external/croppie.min.js";

class Profile {
  constructor() {
    // Add a hash to the url if one doesn't exist
    if (location.hash === "") {
      location.hash = "bio";
    }

    // Get the elements
    let profileTabs = document.getElementsByClassName("profile-tab-link");
    let settingsTabs = document.getElementsByClassName("settings-tab-link");
    let tabContent = document.getElementsByClassName("profile-tab-content");
    let settingsTabContent = document.getElementsByClassName(
      "settings-tab-content"
    );

    // Add onclick events to all profile tab buttons
    for (let element of profileTabs) {
      element.onclick = () => {
        // Make all the other tabs inactive
        for (let e of profileTabs) {
          if (e.classList.contains("active")) {
            e.classList.remove("active");
          }
        }
        // Make all other tab content invisible
        for (let e of tabContent) {
          e.style.display = "none";
        }
        // Add active tag to current when clicked
        element.classList.add("active");

        // Make linked content tab visible
        document.getElementById(element.dataset.tabContentId).style.display =
          "block";

        // Add hash to location url to remember current tab if page is reloaded
        location.hash = element.dataset.tabTitle;
      };

      // click the tab saved in the url
      if (location.hash.replace("#", "") == element.dataset.tabTitle) {
        element.click();
      }
    }

    // Settings tabs
    let firstElement = true;
    for (let element of settingsTabs) {
      document.getElementById(element.dataset.tabContentId).style.display =
        "none";

      element.onclick = () => {
        // Make all the other tabs inactive
        for (let e of settingsTabs) {
          if (e.classList.contains("active")) {
            e.classList.remove("active");
          }
        }
        // Make all other tab content invisible
        for (let e of settingsTabContent) {
          e.style.display = "none";
        }
        // Add active tag to current when clicked
        element.classList.add("active");

        // Make linked content tab visible
        document.getElementById(element.dataset.tabContentId).style.display =
          "block";
      };
      if (firstElement) {
        element.click();
        firstElement = false;
      }
    }

    // OnChange event for colour selector
    let profileColourSelector = document.getElementById("profile-colour");
    let profileContentContainer = document.getElementById("content-container");

    if (profileColourSelector) {
      profileColourSelector.onchange = () => {
        profileContentContainer.style.backgroundColor =
          profileColourSelector.value;
      };
    }

    this.croppieUpload = new Croppie(document.getElementById("upload-image"), {
      viewport: {
        width: 220,
        height: 220,
        type: "square",
      },
    });

    // Onchange event for profile picture
    let profilePictureSettings = document.getElementById(
      "profile-settings-profile-picture"
    );
    if (profilePictureSettings) {
      profilePictureSettings.onchange = () => {
        this.readFile(profilePictureSettings);
      };
    }

    document.getElementById("settings-profile").onclick = () => {
      let hiddenPfpField = document.getElementById(
        "hidden-base64-profile-picture"
      );
      let base64Img;
      this.croppieUpload
        .result({
          type: "canvas",
          size: "viewport",
        })
        .then(function (resp) {
          base64Img = resp;
          if (base64Img.length === 6) {
            base64Img = null;
          }
          hiddenPfpField.value = base64Img;
        });
    };
  }

  readFile(input) {
    if (input.files && input.files[0]) {
      let reader = new FileReader();
      reader.onload = (e) => {
        document.getElementById("upload-image").classList.add("ready");
        this.croppieUpload.bind({
          url: e.target.result,
        });
      };
      reader.readAsDataURL(input.files[0]);
    }
  }

  changeSettingsTab(evt, tabName) {
    let tabContent = document.getElementsByClassName("settings-tab-content");
    let tabLinks = document.getElementsByClassName("settings-tab-link");

    for (let tab of tabContent) {
      tab.style.display = "none";
    }

    for (let link of tabLinks) {
      if (link.classList.contains("active")) {
        link.classList.remove("active");
      }
    }

    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.classList.push("active");
  }
}

export { Profile };
