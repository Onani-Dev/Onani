/*
 * @Author: Blakeando
 * @Date:   2020-09-14 00:47:49
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-16 00:44:14
 */
'use strict';

const settingsBio = document.getElementById("profile-settings-bio");
const profilePicSelect = document.getElementById("profile-settings-profile-picture");
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

function SaveAccSettings() {
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
    }).then(function (response) {
      if (response.ok) {
        window.location.hash = "#settings";
        profilePicSelect.value = "";
        location.reload();
      }
    })
  });
}
