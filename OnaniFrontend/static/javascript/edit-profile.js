/*
 * @Author: Blakeando
 * @Date:   2020-09-14 00:47:49
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-14 15:05:38
 */
'use strict';
let editMode = false;
const editButton = document.getElementById("profile-edit-button");

document.addEventListener('DOMContentLoaded', init, false);
function init() {

  editButton.addEventListener("click", function () {
    if (!editMode) {
      editMode = true;
      editButton.innerHTML = "Save Changes";
    }
    else {
      editMode = false;
      editButton.innerHTML = "Edit Profile";
    }
  });
}