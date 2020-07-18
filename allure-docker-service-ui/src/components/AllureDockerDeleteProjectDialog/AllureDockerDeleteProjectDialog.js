import React, { Component } from "react";
import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";

import axios from "../../api/axios-allure-docker";

class AllureDockerDeleteProjectDialog extends Component {
  deleteProject = (projectId) => {
    axios
      .delete(`/projects/${projectId}`)
      .then((response) => {
        this.props.getProjects();
        this.handleAPISuccessAlert(projectId)
      })
      .catch((error) => {
        this.handleAPIErrorAlert(error);
      });
    this.props.handleCloseDialog();
  };

  handleCloseDialog = () => {
    this.props.handleCloseDialog();
  };

  handleAPISuccessAlert = (projectId) => {
    this.props.setAPIAlert(
      "success",
      `Project ${projectId.toUpperCase()} deleted succesfully!`,
      true
    );
  };

  handleAPIErrorAlert = (error) => {
    this.props.setAPIAlert(
      "error",
      `Problems during project deletion => ${error.message}`,
      true
    );
  };

  render() {
    let projectId = "";
    if (this.props.projectId) {
      projectId = this.props.projectId;
    }

    return (
      <Dialog
        open={this.props.open}
        onClose={this.handleCloseDialog}
        aria-labelledby="form-dialog-title"
      >
        <DialogTitle id="form-dialog-title">
          Delete Project {projectId.toUpperCase()}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            You will lose reports related to project {projectId.toUpperCase()}.
            Are you sure to delete this project?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={this.handleCloseDialog} color="primary">
            Cancel
          </Button>
          <Button onClick={() => this.deleteProject(projectId)} color="primary">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    );
  }
}
export default AllureDockerDeleteProjectDialog;
