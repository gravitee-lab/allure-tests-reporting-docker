import React, { Component } from "react";
import "./App.css";
import {
  createMuiTheme,
  ThemeProvider,
  withStyles,
} from "@material-ui/core/styles";
import { blueGrey, red, cyan, orange } from "@material-ui/core/colors";
import Cookies from "universal-cookie";

import axios from "./api/axios-allure-docker";
import AllureDockerBar from "./containers/AllureDockerBar/AllureDockerBar";
import AllureDockerProject from "./containers/AllureDockerProject/AllureDockerProject";
import AllureDockerSnackBar from "./components/AllureDockerSnackBar/AllureDockerSnackBar";

import Test from "./containers/Test/Test";
import withErrorHandler from "./hoc/withErrorHandler/withErrorHandler";

const styles = (theme) => ({
  container: {
    paddingTop: theme.spacing(4),
    paddingBottom: theme.spacing(4),
  },
  content: {
    flexGrow: 1,
    padding: theme.spacing(5),
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },
});

const autoHideDurationAlert = 3000
class App extends Component {
  state = {
    darkState: false,
    projects: [],
    projectSelected: null,
    apiAlert: {
      severity: 'info',
      show: false,
      message: '',
      duration: autoHideDurationAlert,
    }
  };

  componentDidMount() {
    console.log("APP componentDidMount");
    this.getProjects();
  }

  componentDidUpdate(){

  }

  login = () => {
    axios
      .post("/login", {
        username: "username",
        password: "password",
      })
      .then((response) => {
        let token = response.data.data["access_token"];

        const cookies = new Cookies();
        cookies.set("access_token_cookie", token, { path: "/" });
      })
      .catch((error) => {
        //
      });
  };

  selectProject = (projectId) => {
    this.setState({ projectSelected: projectId });
  };

  getProjects = () => {
    axios
      .get("/projects")
      .then((response) => {
        const projects = response.data.data.projects;
        this.setState({ projects: response.data.data.projects });
        if (projects.length !== 0) {
          this.selectProject(Object.keys(projects)[0]);
        }
      })
      .catch((error) => {
        this.setAPIAlert("error", error.message, true);
      });
  };

  setAPIAlert = (severity, message, show) => {
    const apiAlert = { ...this.state.apiAlert };
    apiAlert.severity = severity;
    apiAlert.show = show;
    apiAlert.message = message;
    this.setState({ apiAlert: apiAlert });
  };
  
  resetAPIAlert = () => {
    const apiAlert = { ...this.state.apiAlert };
    apiAlert.show = false;
    apiAlert.message = '';
    apiAlert.duration = autoHideDurationAlert;
    this.setState({ apiAlert: apiAlert });
  };

  handleThemeChange = () => {
    this.setState({ darkState: !this.state.darkState });
  };

  render() {
    const { classes } = this.props;

    const mainPrimaryColor = this.state.darkState ? cyan[300] : blueGrey[800];
    const mainSecondaryColor = this.state.darkState ? cyan[100] : red[500];
    const palletType = this.state.darkState ? "dark" : "light";
    const darkTheme = createMuiTheme({
      palette: {
        type: palletType,
        primary: {
          main: mainPrimaryColor,
        },
        secondary: {
          main: mainSecondaryColor,
        },
      },
    });

    let projects = [];
    if (this.state.projects) {
      projects = this.state.projects;
    }

    return (
      <React.Fragment>
        <ThemeProvider theme={darkTheme}>
          <AllureDockerBar
            elements={projects}
            darkState={this.state.darkState}
            handleThemeChange={this.handleThemeChange}
            selectProject={this.selectProject}
          >
            <main className={classes.content}>
              <AllureDockerSnackBar
                severity={this.state.apiAlert.severity}
                show={this.state.apiAlert.show}
                message={this.state.apiAlert.message}
                duration={this.state.apiAlert.duration}
                resetAPIAlert={this.resetAPIAlert}
              />
              <AllureDockerProject
                projectId={this.state.projectSelected}
                setAPIAlert={this.setAPIAlert}
                getProjects={this.getProjects}
              />
            </main>
          </AllureDockerBar>
        </ThemeProvider>
      </React.Fragment>
    );
  }
}

export default withStyles(styles, { withTheme: true })(App);
