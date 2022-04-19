/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 13:00:29
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-19 13:02:13
 */
// Opening side navigation bar (mobile)
function openNav() {
  document.getElementById("side-navigation").style.width = "250px";
}

// Closing side navigation bar (mobile)
function closeNav() {
  document.getElementById("side-navigation").style.width = "0";
}

export { openNav, closeNav };
