import React, { Component } from "react";
import { withStyles } from "@material-ui/core/styles";
import SpeedDial from "@material-ui/lab/SpeedDial";
import SpeedDialIcon from "@material-ui/lab/SpeedDialIcon";
import SpeedDialAction from "@material-ui/lab/SpeedDialAction";
import FileCopyIcon from "@material-ui/icons/FileCopyOutlined";

import AllureDockerNewProjectDialog from "../AllureDockerNewProjectDialog/AllureDockerNewProjectDialog";

const styles = (theme) => ({
  root: {
    transform: "translateZ(100px)",
    flexGrow: 1,
  },
  speedDial: {
    position: "absolute",
    bottom: theme.spacing(2),
    right: theme.spacing(2),
  },
});

const actions = [
  { icon: <FileCopyIcon />, name: "New Project", key: "new-project" },
];

class AllureDockerSpeedDial extends Component {
  state = {
    open: false,
    openNewProjectDialog: false,
  };

  handleOpen = () => {
    this.setState({ open: true });
  };

  handleClose = () => {
    this.setState({ open: false });
  };

  handleAction = (keyAction) => {
    switch (keyAction) {
      case "new-project":
        this.setState({ openNewProjectDialog: true });
        break;
    }
  };

  closeNewProjectDialog = () => {
    this.setState({ openNewProjectDialog: false });
    this.handleClose();
  };

  render() {
    const { classes } = this.props;

    return (
      <div className={classes.root}>
        <SpeedDial
          ariaLabel="SpeedDial tooltip example"
          className={classes.speedDial}
          icon={<SpeedDialIcon />}
          onClose={this.handleClose}
          onOpen={this.handleOpen}
          open={this.state.open}
          direction="left"
        >
          {actions.map((action) => (
            <SpeedDialAction
              key={action.name}
              icon={action.icon}
              tooltipTitle={action.name}
              tooltipOpen
              onClick={() => this.handleAction(action.key)}
            />
          ))}
        </SpeedDial>
        <AllureDockerNewProjectDialog
          setAPIAlert={this.props.setAPIAlert}
          open={this.state.openNewProjectDialog}
          closeNewProjectDialog={this.closeNewProjectDialog}
          getProjects={this.props.getProjects}
        />
      </div>
    );
  }
}
export default withStyles(styles, { withTheme: true })(AllureDockerSpeedDial);
