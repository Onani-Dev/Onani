/**
 * @Author: kapsikkum
 * @Date:   2022-04-20 23:44:57
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-21 03:42:48
 */
import { Croppie } from "croppie";

class Profile {
  constructor() {
    // Croppie thing
    this.uploadCrop = new Croppie(document.getElementById("upload-image"), {
      viewport: {
        width: 220,
        height: 220,
        type: "square",
      },
    });

    try {
      document.getElementById("account-settings").click();
    } catch (error) {}

    // OnChange event for colour selector
    let profileColourSelector = document.getElementById("profile-colour");
    let profileContentContainer = document.getElementById("content-container");

    if (profileColourSelector) {
      profileColourSelector.onchange = () => {
        profileContentContainer.style.backgroundColor =
          profileColourSelector.value;
      };
    }

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
      this.uploadCrop
        .croppie("result", {
          type: "canvas",
          size: "viewport",
        })
        .then(function (resp) {
          base64Img = resp;
          if (base64Img.length == 6) {
            base64Img = null;
          }
          hiddenPfpField.value = base64Img;
        });
    };
  }

  /**
   * Select the tab to show to the user when the page is loaded.
   */
  selectTab() {
    let windowParams = new URLSearchParams(window.location.search);
    if (
      windowParams.get("t") != "" &&
      ["bio", "settings", "posts"].includes(windowParams.get("t"))
    ) {
      document.getElementById(windowParams.get("t")).click();
    } else {
      document.getElementById("bio").click();
    }
  }

  readFile(input) {
    if (input.files && input.files[0]) {
      let reader = new FileReader();
      reader.onload = function (e) {
        document.getElementById("upload-image").classList.add("ready");
        this.uploadCrop.bind({
          url: e.target.result,
        });
      };
      reader.readAsDataURL(input.files[0]);
    }
  }

  changeTab(evt, tabName) {
    let windowParams = new URLSearchParams(window.location.search);
    let tabContent = document.getElementsByClassName("profile-tab-content");
    let tabLinks = document.getElementsByClassName("profile-tab-link");
    let pageURL = new URL(window.location.href);

    windowParams.set("t", tabName.replace("-tab", ""));

    pageURL.search = windowParams.toString();

    window.history.replaceState({ path: pageURL.href }, "", pageURL.href);

    for (let tab of tabContent) {
      tab.style.display = "none";
    }

    for (let link of tabLinks) {
      if (link.classList.contains("active")) {
        link.classList.remove("active");
      }
    }

    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
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
