/*
 * @Author: kapsikkum
 * @Date:   2020-09-14 00:47:49
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2020-09-21 18:52:11
 */
'use strict';

const curPassword = document.getElementById("profile-settings-current-password"),
  editEmail = document.getElementById("profile-settings-email"),
  editUsername = document.getElementById("profile-settings-name"),
  newConfirmPass = document.getElementById("profile-settings-password-confirm"),
  newPassword = document.getElementById("profile-settings-password"),
  profilePicSelect = document.getElementById("profile-settings-profile-picture"),
  settingsBio = document.getElementById("profile-settings-bio"),
  formAccountSettings = document.getElementById("settings-account"),
  formProfileSettings = document.getElementById("settings-profile");

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

$('#profile-settings-profile-picture').on('change', function () { readFile(this); });

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
