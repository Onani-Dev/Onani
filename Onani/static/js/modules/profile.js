/**
 * @Author: kapsikkum
 * @Date:   2022-04-20 23:44:57
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-08-11 13:51:44
 */
import { Alerter } from "./index.min.js";

class Profile {
  constructor() {
    // Read to submit bool
    this.readyToSubmit = true;
    // Alerter
    this.alerter = new Alerter();

    // Add a hash to the url if one doesn't exist
    if (location.hash === "") {
      location.hash = "bio";
    }

    // Init SimpleMDE
    let interval = setInterval(() => {
      if (
        document.querySelector(
          '[data-tab-content-id="settings-profile-tab"].active'
        )
      ) {
        clearInterval(interval);
        this.simplemde.codemirror.refresh();
      }
    }, 100);

    // Get the elements
    let profileTabs = document.getElementsByClassName("profile-tab-link");
    let settingsTabs = document.getElementsByClassName("settings-tab-link");
    let tabContent = document.getElementsByClassName("profile-tab-content");
    let settingsTabContent = document.getElementsByClassName(
      "settings-tab-content"
    );

    if (settingsTabContent.length > 0) {
      this.simplemde = new SimpleMDE({
        element: document.getElementById("profile-settings-bio"),
        spellChecker: false,
        status: false,
        lineWrapping: true,
      });

      // Init croppie
      this.croppieUpload = new Croppie(
        document.getElementById("upload-image"),
        {
          viewport: {
            width: 220,
            height: 220,
            type: "square",
          },
        }
      );
    }

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
          "flex";

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
          "flex";
      };
      if (firstElement) {
        element.click();
        firstElement = false;
      }
    }

    // Add events for form submit buttons
    let submitButtons = document.getElementsByClassName(
      "profile-settings-submit"
    );
    for (let e of submitButtons) {
      e.onclick = () => {
        if (e.dataset.submitFor === "settings-profile") {
          this.readyToSubmit = false;
          this.cropImage();
        }
        this.submitForm(e.dataset.submitFor);
      };
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

    // Onchange event for profile picture
    let profilePictureSettings = document.getElementById(
      "profile-settings-profile-picture"
    );
    if (profilePictureSettings) {
      profilePictureSettings.onchange = () => {
        this.readFile(profilePictureSettings);
      };
    }
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

  /**
   * Function to crop the image inside of croppie right now.
   */
  cropImage() {
    let hiddenPfpField = document.getElementById(
      "hidden-base64-profile-picture"
    );
    let base64Img;
    this.croppieUpload
      .result({
        type: "canvas",
        size: "viewport",
      })
      .then((resp) => {
        base64Img = resp;
        if (base64Img.length === 6) {
          base64Img = null;
        }
        hiddenPfpField.value = base64Img;
        this.readyToSubmit = true;
      });
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

    document.getElementById(tabName).style.display = "flex";
    evt.currentTarget.classList.push("active");
  }

  // updateProfileInfo(data) {
  //   document.getElementById("profile-bio-textarea").innerText =
  //     data.settings.biography;
  //   document.getElementById("profile-picture-image").src =
  //     data.settings.biography;
  // }

  // Submit settings forms to the api
  submitForm(formID) {
    if (!this.readyToSubmit) {
      setTimeout(() => {
        this.submitForm(formID);
      }, 100);
    } else {
      let formElement = document.getElementById(formID);

      formElement.dispatchEvent(new Event("change"));

      let formData = new FormData(formElement);

      let formJSON = {};
      formData.forEach((value, key) => {
        if (typeof value === "string") {
          if (key === "biography") {
            value = this.simplemde.value();
          }
          formJSON[key] = value;
        }
      });

      let settings = {
        url: "/api/v1/profile",
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        data: JSON.stringify(formJSON),
      };

      $.ajax(settings).always((response) => {
        if (response.status === 429) {
          this.alerter.error("You're doing this too much, Slow down.", true);
        } else if (response.status === 500) {
          this.alerter.error("Internal server error.", true);
        } else {
          this.alerter.success("Settings saved.", true);
          location.reload();
        }
      });
    }
  }
}

export { Profile };
