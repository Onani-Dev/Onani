/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 13:00:29
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-21 00:42:51
 */

class SideNavbarControls {
  constructor() {
    this.sideNav = document.getElementById("side-navigation");

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
    this.sideNav.style.width = "250px";
  }
  // Closing side navigation bar (mobile)
  closeNav() {
    this.sideNav.style.width = "0";
  }
}

export { SideNavbarControls };
