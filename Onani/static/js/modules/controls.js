/**
 * @Author: kapsikkum
 * @Date:   2022-04-19 13:00:29
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-22 00:45:17
 */

class SideNavbarControls {
  constructor() {
    let closeNav = this.closeNav;
    let openNav = this.openNav;
    // Register buttons to open navigation
    document.getElementById("side-navigation-close-button").onclick = () => {
      closeNav();
    };
    document.getElementById("side-navigation-open-button").onclick = () => {
      openNav();
    };
  }

  // Opening side navigation bar (mobile)
  openNav() {
    document.getElementById("side-navigation").style.width = "250px";
  }
  // Closing side navigation bar (mobile)
  closeNav() {
    document.getElementById("side-navigation").style.width = "0";
  }
}

export { SideNavbarControls };
