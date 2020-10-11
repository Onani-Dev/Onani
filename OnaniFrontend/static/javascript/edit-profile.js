/*
 * @Author: kapsikkum
 * @Date:   2020-09-14 00:47:49
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2020-10-11 22:41:33
 */
'use strict';

const curPassword = document.getElementById("profile-settings-current-password"),
  deviantartProfile = document.getElementById("settings-deviantart"),
  discordProfile = document.getElementById("settings-discord"),
  editEmail = document.getElementById("profile-settings-email"),
  editUsername = document.getElementById("profile-settings-name"),
  formAccountSettings = document.getElementById("settings-account"),
  formPlatformSettings = document.getElementById("settings-platforms"),
  formProfileSettings = document.getElementById("settings-profile"),
  formSiteSettings = document.getElementById("settings-site"),
  githubProfile = document.getElementById("settings-github"),
  newConfirmPass = document.getElementById("profile-settings-password-confirm"),
  newPassword = document.getElementById("profile-settings-password"),
  patreonProfile = document.getElementById("settings-patreon"),
  pixivProfile = document.getElementById("settings-pixiv"),
  profilePicSelect = document.getElementById("profile-settings-profile-picture"),
  settingsBio = document.getElementById("profile-settings-bio"),
  twitterProfile = document.getElementById("settings-twitter"),
  tagBlacklist = document.getElementById("profile-settings-blacklist"),
  customCss = document.getElementById("profile-settings-custom-css");

let $uploadCrop;

function readFile(input) {
  if (input.files && input.files[0]) {
    let reader = new FileReader();
    reader.onload = function (e) {
      $('#upload-image').addClass('ready');
      $uploadCrop.croppie('bind', {
        url: e.target.result
      });
    }
    reader.readAsDataURL(input.files[0]);
  }
}

$uploadCrop = $('#upload-image').croppie({
  viewport: {
    width: 220,
    height: 220,
    type: "square"
  },
});

function SaveAccountSettings() {
  fetch("/api/profile/edit", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: editUsername.value,
      email: editEmail.value,
      current_password: curPassword.value,
      new_password: newPassword.value,
      confirm_password: newConfirmPass.value,
    })
  }).then(response => {
    response.json().then(json => {
      if (json.ok) {
        formAccountSettings.reset();
        location.reload();
      } else {
        alert(json.error);
      }
    })
  })
}

function SaveProfileSettings() {
  let base64Img;

  $uploadCrop.croppie('result', {
    type: 'canvas',
    size: 'viewport'
  }).then(function (resp) {
    base64Img = resp;
    if (base64Img.length == 6) {
      base64Img = null;
    }
    fetch("/api/profile/edit", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        bio: settingsBio.value,
        avatar: base64Img
      })
    }).then(response => {
      response.json().then(json => {
        if (json.ok) {
          formProfileSettings.reset();
          location.reload();
        } else {
          alert(json.error);
        }
      })
    })
  });
}

function SavePlatformSettings() {
  let success = true;
  let elements = [deviantartProfile, discordProfile, githubProfile, patreonProfile, pixivProfile, twitterProfile];

  for (let el in elements) {
    el = elements[el];
    if (!el.checkValidity()) {
      success = false;
      alert(`${el.name} is invalid.`);
      break;
    }
  }

  if (success) {
    fetch("/api/profile/edit", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platforms: {
          deviantart: deviantartProfile.value,
          discord: discordProfile.value,
          github: githubProfile.value,
          patreon: patreonProfile.value,
          pixiv: pixivProfile.value,
          twitter: twitterProfile.value,
        }
      })
    }).then(response => {
      response.json().then(json => {
        if (json.ok) {
          formPlatformSettings.reset();
          location.reload();
        } else {
          alert(json.error);
        }
      })
    })
  }
}

function SaveSiteSettings() {
  fetch("/api/profile/edit", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      custom_css: customCss.value,
      tag_blacklist: tagBlacklist.value.split("\n")
    })
  }).then(response => {
    response.json().then(json => {
      if (json.ok) {
        formSiteSettings.reset();
        location.reload();
      } else {
        alert(json.error);
      }
    })
  })
}

$('#profile-settings-profile-picture').on('change', function () { readFile(this); });

// const twitterRegex = /\b((http[s]?:\/\/)?twitter\.com\/[A-z0-9!'#S%&'()*+,\-\./:;<=>?@[/\]^_{|}~]{1,})\b/g,
//   pixivRegex = /\b((http[s]?:\/\/)?(www\.)?pixiv\.net\/[A-z]{1,}\/users\/[\d]{1,})\b/g,
//   patreonRegex = /\b((http[s]?:\/\/)?(www\.)?patreon\.com\/[A-z0-9!'#S%&'()*+,\-\./:;<=>?@[/\]^_{|}~]{1,})\b/g,
//   deviantartRegex = /\b((http[s]?:\/\/)?(www\.)?deviantart\.com\/[A-z0-9!'#S%&'()*+,\-\./:;<=>?@[/\]^_{|}~]{1,})\b/g,
//   discordRegex = /\b([\w\d]{1,32}#[\d]{4,})\b/g;
