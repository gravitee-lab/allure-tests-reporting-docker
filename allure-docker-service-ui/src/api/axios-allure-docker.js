import axios from "axios";
import * as errors from "../api/errors/errors";

const instance = axios.create({
  baseURL: process.env.REACT_APP_ALLURE_DOCKER_URL,
});

instance.interceptors.request.use((request) => {
  return request;
});

instance.interceptors.response.use((response) => {
  return response;
});

instance.interceptors.response.use(undefined, (error) => {
  let message = "";
  let type = "";
  try {
    message = error.response.data["meta_data"].message;
    type = errors.SPECIFIC_ERROR;
  } catch (ex) {
    message = JSON.stringify(error.message);
    type = errors.GENERIC_ERROR;
  }
  return Promise.reject({ message, type });
});

export default instance;
