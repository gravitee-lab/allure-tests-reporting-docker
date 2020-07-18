import React, { Component } from "react";

import Box from "@material-ui/core/Box";
import Button from "@material-ui/core/Button";
import ButtonGroup from "@material-ui/core/ButtonGroup";
import Card from "@material-ui/core/Card";
import CardMedia from "@material-ui/core/CardMedia";
import Container from "@material-ui/core/Container";

import clsx from "clsx";
import Grid from "@material-ui/core/Grid";
import Paper from "@material-ui/core/Paper";
import Link from "@material-ui/core/Link";
import Typography from "@material-ui/core/Typography";
import { withStyles } from "@material-ui/core/styles";

import axios from "../../api/axios-allure-docker";
import AllureDockerReportsDropDown from "../../components/AllureDockerReportsDropDown/AllureDockerReportsDropDown";
import AllureDockerSpeedDial from "../../components/AllureDockerSpeedDial/AllureDockerSpeedDial";
import AllureDockerDeleteProjectDialog from "../../components/AllureDockerDeleteProjectDialog/AllureDockerDeleteProjectDialog";

const styles = (theme) => ({
  container: {
    paddingTop: theme.spacing(4),
    paddingBottom: theme.spacing(4),
  },
  paper: {
    padding: theme.spacing(4, 3, 0, 3),
    display: "flex",
    overflow: "auto",
    flexDirection: "column",
  },
  optionsFixedHeight: {
    height: 150,
  },
  dashBoardFixedHeight: {
    height: 1100,
  },
  cardMedia: {
    height: 1000,
  },
  iframe: {
    height: 1000,
    width: 1500,
  },
  rootButtonGroup: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    "& > *": {
      margin: theme.spacing(1),
    },
  },
});

class AllureDockerProject extends Component {
  constructor(props) {
    super(props);
    this.state = this.initialState;
  }

  get initialState() {
    return {
      project: null,
      reportSelected: null,
      openDeleteProjectDialog: false,
    };
  }

  componentDidUpdate() {
    if (this.props.projectId) {
      if (
        !this.state.project ||
        (this.state.project && this.state.project.id !== this.props.projectId)
      ) {
        this.getProject(this.props.projectId);
      }
    }
  }

  getProject = (projectId) => {
    axios
      .get(`/projects/${projectId}`)
      .then((response) => {
        this.setState({ project: response.data.data.project, reportSelected: null });
      })
      .catch((error) => {
        //TODO
        this.handleAPIErrorAlert(error);
        const project = { ...this.state.project };
        project.id = projectId;
        project.reports = [];
        this.setState({ project: project });
      });
  };

  handleAPIErrorAlert = (error) => {
    this.props.setAPIAlert(
      "error",
      `Problems during project getting => ${error.message}`,
      true
    );
  };

  selectReport = (event) => {
    this.setState({ reportSelected: event.target.value });
  };

  openDeleteProjectDialog = () => {
    this.setState({ openDeleteProjectDialog: true });
  };

  closeDeleteProjectDialog = () => {
    this.setState({ openDeleteProjectDialog: false });
  };

  render() {
    const { classes } = this.props;
    const dashboardFixedHeightPaper = clsx(
      classes.paper,
      classes.dashBoardFixedHeight
    );
    const optionsFixedHeightPaper = clsx(
      classes.paper,
      classes.optionsFixedHeight
    );

    let projectId = "";
    let reports = [];
    let reportIframe = "";
    let reportSelected = "";

    if (this.state.project) {
      const project = this.state.project;
      projectId = project.id;
      if (project.reports && project.reports.length !== 0) {
        reports = project.reports;
        reportIframe = reports[0];
        if (
          this.state.reportSelected &&
          this.state.reportSelected !== reportIframe
        ) {
          reportIframe = this.state.reportSelected;
        }
        reportSelected = reportIframe;
      }
    }

    let buttons = "";
    if (reportSelected) {
      buttons = (
        <ButtonGroup
          size="small"
          color="primary"
          variant="contained"
          aria-label="outlined primary button group"
        >
          <Button
            variant="contained"
            color="secondary"
            onClick={this.openDeleteProjectDialog}
          >
            Delete Project
          </Button>
          <Button>Send Results</Button>
          <Button>Generate Report</Button>
          <Button>Clean Results</Button>
          <Button>Clean History</Button>
          <Button>Get Emailable Report</Button>
          <Button>Export Emailable Report</Button>
          <Button>Export Full Report</Button>
        </ButtonGroup>
      );
      if (!reportSelected.endsWith("latest/index.html")) {
        buttons = (
          <ButtonGroup
            size="small"
            color="primary"
            variant="contained"
            aria-label="outlined primary button group"
          >
            <Button
              variant="contained"
              color="secondary"
              onClick={this.openDeleteProjectDialog}
            >
              Delete Project
            </Button>
            <Button>Send Results</Button>
            <Button>Generate Report</Button>
            <Button>Clean Results</Button>
            <Button>Clean History</Button>
          </ButtonGroup>
        );
      }
    } else {
      buttons = (
        <ButtonGroup
          size="small"
          color="primary"
          variant="contained"
          aria-label="outlined primary button group"
        >
          <Button
            variant="contained"
            color="secondary"
            onClick={this.openDeleteProjectDialog}
          >
            Delete Project
          </Button>
        </ButtonGroup>
      );
    }
    return (
      <React.Fragment>
        <Grid container spacing={8}>
          <Grid item xs={12}>
            <Paper className={classes.paper}>
              <Typography variant="h4" align="left">
                {projectId}
              </Typography>
              <AllureDockerReportsDropDown
                selectReport={this.selectReport}
                reportSelected={reportSelected}
                reports={reports}
              />
              <AllureDockerSpeedDial
                setAPIAlert={this.props.setAPIAlert}
                getProjects={this.props.getProjects}
              />
              {buttons}
              <AllureDockerDeleteProjectDialog
                projectId={this.props.projectId}
                open={this.state.openDeleteProjectDialog}
                handleCloseDialog={this.closeDeleteProjectDialog}
                setAPIAlert={this.props.setAPIAlert}
                getProjects={this.props.getProjects}
              />
            </Paper>
          </Grid>
          <Grid item xs={12}>
            <Paper className={dashboardFixedHeightPaper}>
              <Card>
                <CardMedia
                  className={classes.cardMedia}
                  component="iframe"
                  image={reportIframe}
                  title="Allure Report"
                ></CardMedia>
              </Card>
            </Paper>
          </Grid>
        </Grid>

        {/*
          <Grid container spacing={3}>
            <Box pt={4}></Box>
            <Grid item xs={12} md={8} lg={9}>
              <Paper className={fixedHeightPaper}></Paper>
            </Grid>
            <Grid item xs={12} md={4} lg={3}>
              <Paper className={fixedHeightPaper}></Paper>
            </Grid>
            <Grid item xs={12}>
              <Paper className={classes.paper}></Paper>
            </Grid>
          </Grid>*/}

        {/*
        <Link color="inherit" href="https://material-ui.com/">
          Allure
        </Link>{" "}
        <Typography variant="body2" color="textSecondary" align="center">
          {"Copyright © "}
          <Link color="inherit" href="https://material-ui.com/">
            allure
          </Link>{" "}
          {new Date().getFullYear()}
          {"."}
        </Typography>
        */}
      </React.Fragment>
    );
  }
}
/*
export default withStyles(styles, { withTheme: true })(
  withErrorHandler(AllureDockerProject, axios)
);
*/
export default withStyles(styles, { withTheme: true })(AllureDockerProject);
