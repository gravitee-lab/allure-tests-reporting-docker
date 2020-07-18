import React from "react";

import IconButton from "@material-ui/core/IconButton";
import InfoIcon from '@material-ui/icons/Info';
import Menu from "@material-ui/core/Menu";
import MenuItem from "@material-ui/core/MenuItem";
import Switch from "@material-ui/core/Switch";

import SwaggerLogo from "../../components/SwaggerLogo/SwaggerLogo";

const allureDockerMobileMenu = (props) => {
  return (
    <Menu
      anchorEl={props.anchorEl}
      anchorOrigin={{ vertical: "top", horizontal: "right" }}
      id="primary-search-account-menu-mobile"
      keepMounted
      transformOrigin={{ vertical: "top", horizontal: "right" }}
      open={props.isMobileMenuOpen}
      onClose={props.handleMobileMenuClose}
    >
      <MenuItem>
        <Switch checked={props.darkState} onChange={props.handleThemeChange} />
        <p>Dark Mode</p>
      </MenuItem>
      <MenuItem>
        <IconButton color="inherit">
          <InfoIcon />
        </IconButton>
        <p>Info</p>
      </MenuItem>
      <MenuItem>
        <IconButton color="inherit">
          <SwaggerLogo height="100%" />
        </IconButton>
        <p>Swagger Doc</p>
      </MenuItem>
    </Menu>
  );
};

export default allureDockerMobileMenu;
