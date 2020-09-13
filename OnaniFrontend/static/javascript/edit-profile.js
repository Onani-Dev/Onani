/*
 * @Author: Blakeando
 * @Date:   2020-09-14 00:47:49
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-14 02:13:55
 */
'use strict';
var editMode = false;

document.addEventListener('DOMContentLoaded', init, false);
function init() {
  var button = document.getElementById("profile-edit-button");
  button.addEventListener("click", function () {
    if (!editMode) {
      editMode = true;
      button.innerHTML = "Save Changes";
    }
    else {
      editMode = false;
      button.innerHTML = "Edit Profile";
    }
  });
}