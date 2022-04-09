/*
 * @Author: kapsikkum
 * @Date:   2020-09-14 22:24:47
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-10 04:11:29
 */
const tabcontent = document.getElementsByClassName("profile-tab-content"),
  tablinks = document.getElementsByClassName("profile-tab-link"),
  settingsTabContent = document.getElementsByClassName("settings-tab-content"),
  settingsTabLinks = document.getElementsByClassName("settings-tab-link"),
  pageURL = new URL(window.location.href),
  windowParams = new URLSearchParams(window.location.search),
  hiddenPfpField = document.getElementById("hidden-base64-profile-picture"),
  profileColourSelector = document.getElementById("profile-colour"),
  profileContentContainer = document.getElementById("content-container");

let $uploadCrop,
  converter = new showdown.Converter();

function readFile(input) {
  if (input.files && input.files[0]) {
    let reader = new FileReader();
    reader.onload = function (e) {
      $("#upload-image").addClass("ready");
      $uploadCrop.croppie("bind", {
        url: e.target.result,
      });
    };
    reader.readAsDataURL(input.files[0]);
  }
}

$uploadCrop = $("#upload-image").croppie({
  viewport: {
    width: 220,
    height: 220,
    type: "square",
  },
});

if (
  windowParams.get("t") != "" &&
  ["bio", "settings", "posts"].includes(windowParams.get("t"))
) {
  document.getElementById(windowParams.get("t")).click();
} else {
  document.getElementById("bio").click();
}

function changeTab(evt, tabName) {
  windowParams.set("t", tabName.replace("-tab", ""));
  pageURL.search = windowParams.toString();
  window.history.replaceState({ path: pageURL.href }, "", pageURL.href);

  for (var i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

function changeSettingsTab(evt, tabName) {
  for (var i = 0; i < settingsTabContent.length; i++) {
    settingsTabContent[i].style.display = "none";
  }

  for (i = 0; i < settingsTabLinks.length; i++) {
    settingsTabLinks[i].className = settingsTabLinks[i].className.replace(
      " active",
      ""
    );
  }

  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

function CopyText(text) {
  const listener = function (ev) {
    ev.preventDefault();
    ev.clipboardData.setData("text/html", text);
    ev.clipboardData.setData("text/plain", text);
  };
  document.addEventListener("copy", listener);
  document.execCommand("copy");
  document.removeEventListener("copy", listener);
  alert("Copied to clipboard!");
}

try {
  document.getElementById("account-settings").click();
} catch (error) {}

const customEmotes = /(:don:|:katsu:|:desuwa:|:dirt:|:armagan:)/g,
  emojiTable = {
    don: "/static/svg/don.svg",
    katsu: "/static/svg/katsu.svg",
    desuwa: "/static/svg/desuwa.svg",
    dirt: "/static/image/dirt_small.gif",
    armagan: "/static/image/armagan_small.gif",
  };
let bioText = document.getElementById("profile-bio-textarea");
twemoji.parse(document.getElementById("profile-username-header"));
twemoji.parse(bioText);
bioText.innerHTML = bioText.innerHTML.replace(customEmotes, (current) => {
  return `<img src='${
    emojiTable[current.replace(/:/g, "")]
  }' class='emoji' draggable='false' alt='${current}'></img>`;
});
bioText.innerHTML = converter.makeHtml(bioText.innerHTML);

$("#profile-settings-profile-picture").on("change", function () {
  readFile(this);
});

$("#settings-profile").submit(function () {
  let base64Img;
  $uploadCrop
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
});

profileColourSelector.onchange = function (e) {
  profileContentContainer.style.backgroundColor = profileColourSelector.value;
};
