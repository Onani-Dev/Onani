/**
 * @Author: kapsikkum
 * @Date:   2022-04-21 18:33:12
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-22 00:47:03
 */
import {
  ElementFormatter,
  PostsSearch,
  SideNavbarControls,
} from "./modules/index.min.js";

// Formatter
let formatter = new ElementFormatter();
formatter.formatAll();

// Search box
let search = new PostsSearch();

// Mobile sidenav
let sideNav = new SideNavbarControls();
