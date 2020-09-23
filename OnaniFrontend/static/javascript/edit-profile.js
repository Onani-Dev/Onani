/*
 * @Author: kapsikkum
 * @Date:   2020-09-14 00:47:49
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2020-09-24 02:29:56
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
  githubProfile = document.getElementById("settings-github"),
  newConfirmPass = document.getElementById("profile-settings-password-confirm"),
  newPassword = document.getElementById("profile-settings-password"),
  patreonProfile = document.getElementById("settings-patreon"),
  pixivProfile = document.getElementById("settings-pixiv"),
  profilePicSelect = document.getElementById("profile-settings-profile-picture"),
  settingsBio = document.getElementById("profile-settings-bio"),
  twitterProfile = document.getElementById("settings-twitter");

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
    width: 200,
    height: 200,
    type: 'square'
  }
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
  // let success = true;

  // if (success) {
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
  // }
}

$('#profile-settings-profile-picture').on('change', function () { readFile(this); });

twitterProfile.onkeyup = function () {
  if (/\b((http[s]?:\/\/)?twitter\.com\/[A-z0-9!'#S%&'()*+,\-\./:;<=>?@[/\]^_{|}~]{1,})\b/g.test(twitterProfile.value) || twitterProfile.value == "") {
    twitterProfile.setCustomValidity("");
  } else {
    twitterProfile.setCustomValidity("This is not a twitter profile link!");
    twitterProfile.reportValidity();
  }
}

pixivProfile.onkeyup = function () {
  if (/\b((http[s]?:\/\/)?(www\.)?pixiv\.net\/[A-z]{1,}\/users\/[\d]{1,})\b/g.test(pixivProfile.value) || pixivProfile.value == "") {
    pixivProfile.setCustomValidity("");
  } else {
    pixivProfile.setCustomValidity("This is not a Pixiv profile link!");
    pixivProfile.reportValidity();
  }
}

patreonProfile.onkeyup = function () {
  if (/\b((http[s]?:\/\/)?(www\.)patreon\.com\/[A-z0-9!'#S%&'()*+,\-\./:;<=>?@[/\]^_{|}~]{1,})\b/g.test(patreonProfile.value) || patreonProfile.value == "") {
    patreonProfile.setCustomValidity("");
  } else {
    patreonProfile.setCustomValidity("This is not a Patreon page link!");
    patreonProfile.reportValidity();
  }
}

deviantartProfile.onkeyup = function () {
  if (/\b((http[s]?:\/\/)?(www\.)deviantart\.com\/[A-z0-9!'#S%&'()*+,\-\./:;<=>?@[/\]^_{|}~]{1,})\b/g.test(deviantartProfile.value) || deviantartProfile.value == "") {
    deviantartProfile.setCustomValidity("");
  } else {
    deviantartProfile.setCustomValidity("This is not a DeviantArt profile link!");
    deviantartProfile.reportValidity();
  }
}

discordProfile.onkeyup = function () {
  if (/\b([\w\d]{1,32}#[\d]{4,})\b/g.test(discordProfile.value) || discordProfile.value == "") {
    discordProfile.setCustomValidity("");
  } else {
    discordProfile.setCustomValidity("This is not a valid discord username#tag!");
    discordProfile.reportValidity();
  }
}


// function validatePassword() {
//   if (password.value != confirmPassword.value) {

//   } else {
//     confirmPassword.setCustomValidity('');
//   }
// }
// password.onchange = validatePassword;
// confirmPassword.onkeyup = validatePassword;