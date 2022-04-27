/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 13:00:29
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-27 19:05:21
 */

class SideNavbarControls {
  constructor() {
    // Register buttons to open navigation
    document.getElementById("side-navigation-close-button").onclick = () => {
      this.closeNav();
    };
    document.getElementById("side-navigation-open-button").onclick = () => {
      this.openNav();
    };
  }

  // Opening side navigation bar (mobile)
  openNav() {
    document.getElementById("side-navigation").style.width = "16em";
  }
  // Closing side navigation bar (mobile)
  closeNav() {
    document.getElementById("side-navigation").style.width = "0";
  }
}

export { SideNavbarControls };
