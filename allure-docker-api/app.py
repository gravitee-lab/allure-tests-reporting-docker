#pylint: disable=too-many-lines
from logging.config import dictConfig
from functools import wraps
from subprocess import call
import base64
import glob
import io
import json
import os
import re
import shutil
import tempfile
import subprocess
import zipfile
import waitress
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask import (
    Flask, jsonify, render_template, redirect,
    request, send_file, send_from_directory, url_for
)
from flask.logging import create_logger
from flask_swagger_ui import get_swaggerui_blueprint
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, verify_jwt_in_request, jwt_refresh_token_required, get_raw_jwt
)

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(levelname)s]: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__) #pylint: disable=invalid-name
CORS(app)
LOGGER = create_logger(app)
app.config['JWT_SECRET_KEY'] = os.urandom(16)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

DEV_MODE = 0
HOST = '0.0.0.0'
PORT = os.environ['PORT']
THREADS = 7
URL_SCHEME = 'http'
ENABLE_SECURITY_LOGIN = False
SECURITY_USER = None
SECURITY_PASS = None

GENERATE_REPORT_PROCESS = '{}/generateAllureReport.sh'.format(os.environ['ROOT'])
KEEP_HISTORY_PROCESS = '{}/keepAllureHistory.sh'.format(os.environ['ROOT'])
CLEAN_HISTORY_PROCESS = '{}/cleanAllureHistory.sh'.format(os.environ['ROOT'])
CLEAN_RESULTS_PROCESS = '{}/cleanAllureResults.sh'.format(os.environ['ROOT'])
RENDER_EMAIL_REPORT_PROCESS = '{}/renderEmailableReport.sh'.format(os.environ['ROOT'])
ALLURE_VERSION = os.environ['ALLURE_VERSION']
STATIC_CONTENT = os.environ['STATIC_CONTENT']
PROJECTS_DIRECTORY = os.environ['STATIC_CONTENT_PROJECTS']
EMAILABLE_REPORT_FILE_NAME = os.environ['EMAILABLE_REPORT_FILE_NAME']
ORIGIN = 'api'

REPORT_INDEX_FILE = 'index.html'
DEFAULT_TEMPLATE = 'default.html'
EMAILABLE_REPORT_CSS = "https://stackpath.bootstrapcdn.com/bootswatch/4.3.1/cosmo/bootstrap.css"
EMAILABLE_REPORT_TITLE = "Emailable Report"
API_RESPONSE_LESS_VERBOSE = 0

if "EMAILABLE_REPORT_CSS_CDN" in os.environ:
    EMAILABLE_REPORT_CSS = os.environ['EMAILABLE_REPORT_CSS_CDN']
    LOGGER.info('Overriding CSS for Emailable Report. EMAILABLE_REPORT_CSS_CDN=%s',
                EMAILABLE_REPORT_CSS)

if "EMAILABLE_REPORT_TITLE" in os.environ:
    EMAILABLE_REPORT_TITLE = os.environ['EMAILABLE_REPORT_TITLE']
    LOGGER.info('Overriding Title for Emailable Report. EMAILABLE_REPORT_TITLE=%s',
                EMAILABLE_REPORT_TITLE)

if "API_RESPONSE_LESS_VERBOSE" in os.environ:
    try:
        API_RESPONSE_LESS_VERBOSE = int(os.environ['API_RESPONSE_LESS_VERBOSE'])
        LOGGER.info('Overriding API_RESPONSE_LESS_VERBOSE=%s', API_RESPONSE_LESS_VERBOSE)
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting API_RESPONSE_LESS_VERBOSE=0 by default')

if "DEV_MODE" in os.environ:
    try:
        DEV_MODE = int(os.environ['DEV_MODE'])
        LOGGER.info('Overriding DEV_MODE=%s', DEV_MODE)
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting DEV_MODE=0 by default')

if "TLS" in os.environ:
    try:
        IS_ITLS = int(os.environ['TLS'])
        if IS_ITLS == 1:
            URL_SCHEME = 'https'
            LOGGER.info('Enabling TLS=%s', IS_ITLS)
    except Exception as ex:
        LOGGER.error('Wrong env var value. Setting TLS=0 by default')

if "SECURITY_USER" in os.environ:
    SECURITY_USER_TMP = os.environ['SECURITY_USER']
    if SECURITY_USER_TMP and SECURITY_USER_TMP.strip():
        SECURITY_USER = SECURITY_USER_TMP.lower()
        LOGGER.info('Setting SECURITY_USER')

if "SECURITY_PASS" in os.environ:
    SECURITY_PASS_TMP = os.environ['SECURITY_PASS']
    if SECURITY_PASS_TMP and SECURITY_PASS_TMP.strip():
        SECURITY_PASS = SECURITY_PASS_TMP
        LOGGER.info('Setting SECURITY_PASS')

if SECURITY_USER and SECURITY_PASS:
    ENABLE_SECURITY_LOGIN = True
    LOGGER.info('Enabling Security Login. ENABLE_SECURITY_LOGIN=True')

def get_file_as_string(path_file):
    file = None
    content = None
    try:
        file = open(path_file, "r")
        content = file.read()
    except Exception as ex:
        LOGGER.error(str(ex))
    finally:
        if file is not None:
            file.close()
    return content

def generate_security_swagger_specification():
    specs_path = 'swagger/security_specs'
    login_endpoint_spec = get_file_as_string(
        "{}/{}/login_spec.json".format(STATIC_CONTENT, specs_path))
    logout_endpoint_spec = get_file_as_string(
        "{}/{}/logout_spec.json".format(STATIC_CONTENT, specs_path))
    logout_refresh_token_endpoint_spec = get_file_as_string(
        "{}/{}/logout_refresh_token_spec.json".format(STATIC_CONTENT, specs_path))
    refresh_endpoint_spec = get_file_as_string(
        "{}/{}/refresh_spec.json".format(STATIC_CONTENT, specs_path))
    security_schemes = get_file_as_string(
        "{}/{}/security_schemes.json".format(STATIC_CONTENT, specs_path))
    login_scheme = get_file_as_string(
        "{}/{}/login_scheme.json".format(STATIC_CONTENT, specs_path))
    security_response = get_file_as_string(
        "{}/{}/security_response.json".format(STATIC_CONTENT, specs_path))

    try:
        with open("{}/swagger/swagger.json".format(STATIC_CONTENT)) as json_file:
            data = json.load(json_file)

            data['tags'].insert(1, {"name":"Security", "description":""})
            data['paths']['/login'] = eval(login_endpoint_spec) #pylint: disable=eval-used
            data['paths']['/logout'] = eval(logout_endpoint_spec) #pylint: disable=eval-used
            data['paths']['/logout-refresh-token'] = eval(logout_refresh_token_endpoint_spec) #pylint: disable=eval-used
            data['paths']['/refresh'] = eval(refresh_endpoint_spec) #pylint: disable=eval-used
            data['components']['securitySchemes'] = eval(security_schemes) #pylint: disable=eval-used
            data['components']['schemas']['login'] = eval(login_scheme) #pylint: disable=eval-used

            ensure_tags = ['Action', 'Project']
            for path in data['paths']:
                for method in data['paths'][path]:
                    if set(ensure_tags) & set(data['paths'][path][method]['tags']):
                        data['paths'][path][method]['security'] = [{"bearerAuth": []}]
                        data['paths'][path][method]['responses']['401'] = eval(security_response) #pylint: disable=eval-used

        with open("{}/swagger/swagger_security.json".format(STATIC_CONTENT), 'w') as outfile:
            json.dump(data, outfile)
    except Exception as ex:
        LOGGER.error(str(ex))

### swagger specific ###
SWAGGER_URL = '/allure-docker-service/swagger'
API_URL = '/allure-docker-service/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Allure Docker Service"}
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
### end swagger specific ###

### Security Section
if ENABLE_SECURITY_LOGIN:
    generate_security_swagger_specification()

blacklist = set() #pylint: disable=invalid-name
jwt = JWTManager(app) #pylint: disable=invalid-name

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return jti in blacklist

@jwt.invalid_token_loader
def invalid_token_loader(msg):
    return jsonify({
        'meta_data': {
            'message': 'Invalid Token - {}'.format(msg)
        }
    }), 401

@jwt.unauthorized_loader
def unauthorized_loader(msg):
    return jsonify({
        'meta_data': {
            'message': msg
        }
    }), 401

@jwt.expired_token_loader
def my_expired_token_callback(expired_token):
    token_type = expired_token['type']
    return jsonify({
        'meta_data': {
            'message': 'The {} token has expired'.format(token_type),
            'sub_status': 42,
        }
    }), 401

@jwt.revoked_token_loader
def revoked_token_loader():
    return jsonify({
        'meta_data': {
            'message': 'Revoked Token'
        }
    }), 401

def jwt_required(fn):  #pylint: disable=invalid-name, function-redefined
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if ENABLE_SECURITY_LOGIN:
            verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper
### end Security Section

### Security Endpoints Section
@app.route('/login', methods=['POST'], strict_slashes=False)
@app.route('/allure-docker-service/login', methods=['POST'], strict_slashes=False)
def login_endpoint():
    try:
        content_type = str(request.content_type)
        if content_type is None and content_type.startswith('application/json') is False:
            raise Exception("Header 'Content-Type' must be 'application/json'")

        if not request.is_json:
            raise Exception("Missing JSON in body request")

        username = request.json.get('username', None)
        if not username:
            raise Exception("Missing 'username' attribute")

        password = request.json.get('password', None)
        if not password:
            raise Exception("Missing 'password' attribute")

        if SECURITY_USER != username.lower() or SECURITY_PASS != password:
            return jsonify({'meta_data': {'message' : 'Invalid username/password'}}), 401

        json_body = {
            'data': {
                'access_token': create_access_token(identity=SECURITY_USER),
                'refresh_token': create_refresh_token(identity=SECURITY_USER)},
            'meta_data': {'message' : 'Successfully logged'}
        }
        return jsonify(json_body), 200
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route('/logout', methods=['DELETE'], strict_slashes=False)
@app.route('/allure-docker-service/logout', methods=['DELETE'], strict_slashes=False)
@jwt_required
def logout_endpoint():
    jti = get_raw_jwt()['jti']
    blacklist.add(jti)
    return jsonify({'meta_data': {'message' : 'Successfully logged out'}}), 200

@app.route('/logout-refresh-token', methods=['DELETE'], strict_slashes=False)
@app.route('/allure-docker-service/logout-refresh-token', methods=['DELETE'], strict_slashes=False)
@jwt_refresh_token_required
def logout_refresh_token_endpoint():
    jti = get_raw_jwt()['jti']
    blacklist.add(jti)
    return jsonify({'meta_data': {'message' : 'Successfully logged out'}}), 200

@app.route('/refresh', methods=['POST'], strict_slashes=False)
@app.route('/allure-docker-service/refresh', methods=['POST'], strict_slashes=False)
@jwt_refresh_token_required
def refresh_endpoint():
    current_user = get_jwt_identity()
    json_body = {
        'data': {
            'access_token': create_access_token(identity=current_user)
        },
        'meta_data': {
            'message' : 'Successfully token obtained'
        }
    }
    return jsonify(json_body), 200
### end Security Endpoints Section

@app.route("/", strict_slashes=False)
@app.route("/allure-docker-service", strict_slashes=False)
def index_endpoint():
    try:
        return render_template('index.html')
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/swagger.json")
@app.route("/allure-docker-service/swagger.json", strict_slashes=False)
def swagger_json_endpoint():
    try:
        specification_file = 'swagger.json'
        if ENABLE_SECURITY_LOGIN:
            specification_file = 'swagger_security.json'

        return send_file("{}/swagger/{}"
                         .format(STATIC_CONTENT, specification_file), mimetype='application/json')
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/version", strict_slashes=False)
@app.route("/allure-docker-service/version", strict_slashes=False)
def version_endpoint():
    file = None
    try:
        file = open(ALLURE_VERSION, "r")
        version = file.read()
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'data': {
                'version': version.strip()
            },
            'meta_data': {
                'message' : "Version successfully obtained"
            }
        }
        resp = jsonify(body)
        resp.status_code = 200
    finally:
        if file is not None:
            file.close()

    return resp

@app.route("/ui/<path:path>")
@app.route("/allure-docker-service/ui/<path:path>")
def ui_endpoint(path):
    try:
        return send_from_directory('{}/ui'.format(STATIC_CONTENT), path)
    except Exception:
        return send_from_directory('{}/ui'.format(STATIC_CONTENT), 'index.html')

@app.errorhandler(404)
def handle_not_found(error):
    path = str(request.path)
    if path.endswith('ui/') or path.endswith('ui'):
        return send_from_directory('{}/ui'.format(STATIC_CONTENT), 'index.html')

    body = {
        'meta_data': {
            'message' : "Path '{}' - {}".format(path, error)
        }
    }
    resp = jsonify(body)
    resp.status_code = 404
    return resp

@app.route("/latest-report", strict_slashes=False)
@app.route("/allure-docker-service/latest-report", strict_slashes=False)
@jwt_required
def latest_report_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        project_report_latest_path = '/latest/{}'.format(REPORT_INDEX_FILE)
        url = url_for('get_reports_endpoint', project_id=project_id,
                      path=project_report_latest_path, redirect='false', _external=True)
        return redirect(url)
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/send-results", methods=['POST'], strict_slashes=False)
@app.route("/allure-docker-service/send-results", methods=['POST'], strict_slashes=False)
@jwt_required
def send_results_endpoint():
    try:
        content_type = str(request.content_type)
        if content_type is None:
            raise Exception("Header 'Content-Type' should start with 'application/json' or 'multipart/form-data'") #pylint: disable=line-too-long

        if (
                content_type.startswith('application/json') is False and
                content_type.startswith('multipart/form-data') is False
            ):
            raise Exception("Header 'Content-Type' should start with 'application/json' or 'multipart/form-data'") #pylint: disable=line-too-long

        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        validated_results = []
        processed_files = []
        failed_files = []
        results_project = '{}/results'.format(get_project_path(project_id))

        if content_type.startswith('application/json') is True:
            json_body = request.get_json()

            if 'results' not in json_body:
                raise Exception("'results' array is required in the body")

            validated_results = validate_json_results(json_body['results'])
            send_json_results(results_project, validated_results, processed_files, failed_files)

        if content_type.startswith('multipart/form-data') is True:
            validated_results = validate_files_array(request.files.getlist('files[]'))
            send_files_results(results_project, validated_results, processed_files, failed_files)

        failed_files_count = len(failed_files)
        if failed_files_count > 0:
            raise Exception('Problems with files: {}'.format(failed_files))

        if API_RESPONSE_LESS_VERBOSE != 1:
            files = os.listdir(results_project)
            current_files_count = len(files)
            sent_files_count = len(validated_results)
            processed_files_count = len(processed_files)

    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        if API_RESPONSE_LESS_VERBOSE != 1:
            body = {
                'data': {
                    'current_files': files,
                    'current_files_count': current_files_count,
                    'failed_files': failed_files,
                    'failed_files_count': failed_files_count,
                    'processed_files': processed_files,
                    'processed_files_count': processed_files_count,
                    'sent_files_count': sent_files_count
                    },
                'meta_data': {
                    'message' : "Results successfully sent for project_id '{}'".format(project_id)
                }
            }
        else:
            body = {
                'meta_data': {
                    'message' : "Results successfully sent for project_id '{}'".format(project_id)
                }
            }

        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/generate-report", strict_slashes=False)
@app.route("/allure-docker-service/generate-report", strict_slashes=False)
@jwt_required
def generate_report_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        files = None
        project_path = get_project_path(project_id)
        results_project = '{}/results'.format(project_path)

        if API_RESPONSE_LESS_VERBOSE != 1:
            files = os.listdir(results_project)

        execution_name = request.args.get('execution_name')
        if execution_name is None or not execution_name:
            execution_name = 'Execution On Demand'

        execution_from = request.args.get('execution_from')
        if execution_from is None or not execution_from:
            execution_from = ''

        execution_type = request.args.get('execution_type')
        if execution_type is None or not execution_type:
            execution_type = ''

        check_process(KEEP_HISTORY_PROCESS, project_id)
        check_process(GENERATE_REPORT_PROCESS, project_id)

        exec_store_results_process = '1'

        call([KEEP_HISTORY_PROCESS, project_id, ORIGIN])
        response = subprocess.Popen([
            GENERATE_REPORT_PROCESS, exec_store_results_process,
            project_id, ORIGIN, execution_name, execution_from, execution_type],
                                    stdout=subprocess.PIPE).communicate()[0]
        call([RENDER_EMAIL_REPORT_PROCESS, project_id, ORIGIN])

        build_order = 'latest'
        for line in response.decode("utf-8").split("\n"):
            if line.startswith("BUILD_ORDER"):
                build_order = line[line.index(':') + 1: len(line)]

        report_url = url_for('get_reports_endpoint', project_id=project_id,
                             path='{}/index.html'.format(build_order), _external=True)
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        if files is not None:
            body = {
                'data': {
                    'report_url': report_url,
                    'allure_results_files': files
                },
                'meta_data': {
                    'message' : "Report successfully generated for project_id '{}'"
                                .format(project_id)
                }
            }
        else:
            body = {
                'data': {
                    'report_url': report_url
                },
                'meta_data': {
                    'message' : "Report successfully generated for project_id '{}'"
                                .format(project_id)
                }
            }

        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/clean-history", strict_slashes=False)
@app.route("/allure-docker-service/clean-history", strict_slashes=False)
@jwt_required
def clean_history_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(CLEAN_HISTORY_PROCESS, project_id)

        call([CLEAN_HISTORY_PROCESS, project_id, ORIGIN])
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'meta_data': {
                'message' : "History successfully cleaned for project_id '{}'".format(project_id)
            }
        }
        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/clean-results", strict_slashes=False)
@app.route("/allure-docker-service/clean-results", strict_slashes=False)
@jwt_required
def clean_results_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(GENERATE_REPORT_PROCESS, project_id)
        check_process(CLEAN_RESULTS_PROCESS, project_id)

        call([CLEAN_RESULTS_PROCESS, project_id, ORIGIN])
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'meta_data': {
                'message' : "Results successfully cleaned for project_id '{}'".format(project_id)
            }
        }
        resp = jsonify(body)
        resp.status_code = 200

    return resp

@app.route("/emailable-report/render", strict_slashes=False)
@app.route("/allure-docker-service/emailable-report/render", strict_slashes=False)
@jwt_required
def emailable_report_render_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(GENERATE_REPORT_PROCESS, project_id)

        project_path = get_project_path(project_id)
        tcs_latest_report_project = "{}/reports/latest/data/test-cases/*.json".format(project_path)

        files = glob.glob(tcs_latest_report_project)
        test_cases = []
        for file_name in files:
            with open(file_name) as file:
                json_string = file.read()
                LOGGER.debug("----TestCase-JSON----")
                LOGGER.debug(json_string)
                test_case = json.loads(json_string)
                if test_case["hidden"] is False:
                    test_cases.append(test_case)

        server_url = url_for('latest_report_endpoint', project_id=project_id, _external=True)

        if "SERVER_URL" in os.environ:
            LOGGER.info('Overriding Allure Server Url')
            server_url = os.environ['SERVER_URL']

        report = render_template(DEFAULT_TEMPLATE, css=EMAILABLE_REPORT_CSS,
                                 title=EMAILABLE_REPORT_TITLE, projectId=project_id,
                                 serverUrl=server_url, testCases=test_cases)

        emailable_report_path = '{}/reports/{}'.format(project_path, EMAILABLE_REPORT_FILE_NAME)
        file = None
        try:
            file = open(emailable_report_path, "w")
            file.write(report)
        finally:
            if file is not None:
                file.close()
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp
    else:
        return report

@app.route("/emailable-report/export", strict_slashes=False)
@app.route("/allure-docker-service/emailable-report/export", strict_slashes=False)
@jwt_required
def emailable_report_export_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(GENERATE_REPORT_PROCESS, project_id)

        project_path = get_project_path(project_id)
        emailable_report_path = '{}/reports/{}'.format(project_path, EMAILABLE_REPORT_FILE_NAME)

        report = send_file(emailable_report_path, as_attachment=True)
    except Exception as ex:
        message = str(ex)

        body = {
            'meta_data': {
                'message' : message
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp
    else:
        return report

@app.route("/report/export", strict_slashes=False)
@app.route("/allure-docker-service/report/export", strict_slashes=False)
@jwt_required
def report_export_endpoint():
    try:
        project_id = resolve_project(request.args.get('project_id'))
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        check_process(GENERATE_REPORT_PROCESS, project_id)

        project_path = get_project_path(project_id)
        tmp_report = '{}/allure-report'.format(tempfile.mkdtemp())
        shutil.copytree('{}/reports/latest'.format(project_path), tmp_report)

        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as zipf:
            root_dir = os.path.basename(tmp_report)
            for dirpath, dirnames, files in os.walk(tmp_report): #pylint: disable=unused-variable
                for file in files:
                    file_path = os.path.join(dirpath, file)
                    parent_path = os.path.relpath(file_path, tmp_report)
                    zipf.write(file_path, os.path.join(root_dir, parent_path))
        data.seek(0)

        shutil.rmtree(tmp_report, ignore_errors=True)

        return send_file(
            data,
            mimetype='application/zip',
            as_attachment=True,
            attachment_filename='allure-docker-service-report.zip'
        )
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route("/projects", methods=['POST'], strict_slashes=False)
@app.route("/allure-docker-service/projects", methods=['POST'], strict_slashes=False)
@jwt_required
def create_project_endpoint():
    try:
        if not request.is_json:
            raise Exception("Header 'Content-Type' is not 'application/json'")

        json_body = request.get_json()

        if 'id' not in json_body:
            raise Exception("'id' is required in the body")

        if isinstance(json_body['id'], str) is False:
            raise Exception("'id' should be string")

        if not json_body['id'].strip():
            raise Exception("'id' should not be empty")

        project_id_pattern = re.compile('^[a-z\\d]([a-z\\d -]*[a-z\\d])?$')
        match = project_id_pattern.match(json_body['id'])
        if  match is None:
            raise Exception("'id' should contains alphanumeric lowercase characters or hyphens. For example: 'my-project-id'") #pylint: disable=line-too-long

        project_id = json_body['id']
        if is_existent_project(project_id) is True:
            raise Exception("project_id '{}' is existent".format(project_id))

        if project_id == 'default':
            raise Exception("The id 'default' is not allowed. Try with another project_id")

        project_path = get_project_path(project_id)
        latest_report_project = '{}/reports/latest'.format(project_path)
        results_project = '{}/results'.format(project_path)

        if not os.path.exists(latest_report_project):
            os.makedirs(latest_report_project)

        if not os.path.exists(results_project):
            os.makedirs(results_project)
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'data': {
                'id': project_id,
            },
            'meta_data': {
                'message' : "Project successfully created"
            }
        }
        resp = jsonify(body)
        resp.status_code = 201
    return resp

@app.route('/projects/<project_id>', methods=['DELETE'], strict_slashes=False)
@app.route("/allure-docker-service/projects/<project_id>", methods=['DELETE'], strict_slashes=False)
@jwt_required
def delete_project_endpoint(project_id):
    try:
        if project_id == 'default':
            raise Exception("You must not remove project_id 'default'. Try with other projects")

        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        project_path = get_project_path(project_id)
        shutil.rmtree(project_path)
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
    else:
        body = {
            'meta_data': {
                'message' : "project_id: '{}' successfully removed".format(project_id)
            }
        }
        resp = jsonify(body)
        resp.status_code = 200
    return resp

@app.route('/projects/<project_id>', strict_slashes=False)
@app.route("/allure-docker-service/projects/<project_id>", strict_slashes=False)
@jwt_required
def get_project_endpoint(project_id):
    try:
        if is_existent_project(project_id) is False:
            body = {
                'meta_data': {
                    'message' : "project_id '{}' not found".format(project_id)
                }
            }
            resp = jsonify(body)
            resp.status_code = 404
            return resp

        project_reports_path = '{}/reports'.format(get_project_path(project_id))
        reports_entity = []

        directories = os.listdir(project_reports_path)
        for file in directories:
            file_path = '{}/{}/index.html'.format(project_reports_path, file)
            is_file = os.path.isfile(file_path)
            if is_file is True:
                report = url_for('get_reports_endpoint', project_id=project_id,
                                 path='{}/index.html'.format(file), _external=True)
                reports_entity.append([report, os.path.getmtime(file_path), file])

        reports_entity.sort(key=lambda reports_entity: reports_entity[1], reverse=True)
        reports = []
        latest_report = None
        for report_entity in reports_entity:
            link = report_entity[0]
            if report_entity[2].lower() != 'latest':
                reports.append(link)
            else:
                latest_report = link

        if latest_report is not None:
            reports.insert(0, latest_report)

        body = {
            'data': {
                'project': {
                    'id': project_id,
                    'reports': reports
                },
            },
            'meta_data': {
                'message' : "Project successfully obtained"
                }
            }
        resp = jsonify(body)
        resp.status_code = 200
        return resp
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route('/projects', strict_slashes=False)
@app.route("/allure-docker-service/projects", strict_slashes=False)
@jwt_required
def get_projects_endpoint():
    try:
        directories = os.listdir(PROJECTS_DIRECTORY)
        projects = {}
        for project_name in directories:
            is_dir = os.path.isdir('{}/{}'.format(PROJECTS_DIRECTORY, project_name))
            if is_dir is True:
                project = {}
                project['uri'] = url_for('get_project_endpoint',
                                         project_id=project_name,
                                         _external=True)
                projects[project_name] = project

        body = {
            'data': {
                'projects': projects,
            },
            'meta_data': {
                'message' : "Projects successfully obtained"
                }
            }
        resp = jsonify(body)
        resp.status_code = 200
        return resp
    except Exception as ex:
        body = {
            'meta_data': {
                'message' : str(ex)
            }
        }
        resp = jsonify(body)
        resp.status_code = 400
        return resp

@app.route('/projects/<project_id>/reports/<path:path>')
@app.route("/allure-docker-service/projects/<project_id>/reports/<path:path>")
@jwt_required
def get_reports_endpoint(project_id, path):
    try:
        project_path = '{}/reports/{}'.format(project_id, path)
        return send_from_directory(PROJECTS_DIRECTORY, project_path)
    except Exception:
        if request.args.get('redirect') == 'false':
            return send_from_directory(PROJECTS_DIRECTORY, project_path)
        return redirect(url_for('get_project_endpoint', project_id=project_id, _external=True))


def validate_files_array(files):
    if not files:
        raise Exception("'files[]' array is empty")
    return files

def validate_json_results(results):
    if  isinstance(results, list) is False:
        raise Exception("'results' should be an array")

    if not results:
        raise Exception("'results' array is empty")

    map_results = {}
    for result in results:
        if 'file_name' not in result or not result['file_name'].strip():
            raise Exception("'file_name' attribute is required for all results")
        file_name = result.get('file_name')
        map_results[file_name] = ''

    if len(results) != len(map_results):
        raise Exception("Duplicated file names in 'results'")

    validated_results = []
    for result in results:
        file_name = result.get('file_name')
        validated_result = {}
        validated_result['file_name'] = file_name

        if 'content_base64' not in result or not result['content_base64'].strip():
            raise Exception("'content_base64' attribute is required for '{}' file"
                            .format(file_name))

        content_base64 = result.get('content_base64')
        try:
            validated_result['content_base64'] = base64.b64decode(content_base64)
        except Exception:
            raise Exception("'content_base64' attribute content for '{}' file should be encoded to base64" #pylint: disable=line-too-long
                            .format(file_name))
        validated_results.append(validated_result)

    return validated_results

def send_files_results(results_project, validated_results, processed_files, failed_files):
    for file in validated_results:
        try:
            file_name = secure_filename(file.filename)
            file.save("{}/{}".format(results_project, file_name))
        except Exception as ex:
            error = {}
            error['message'] = str(ex)
            error['file_name'] = file_name
            failed_files.append(error)
        else:
            processed_files.append(file_name)

def send_json_results(results_project, validated_results, processed_files, failed_files):
    for result in validated_results:
        file_name = secure_filename(result.get('file_name'))
        content_base64 = result.get('content_base64')
        file = None
        try:
            file = open("%s/%s" % (results_project, file_name), "wb")
            file.write(content_base64)
        except Exception as ex:
            error = {}
            error['message'] = str(ex)
            error['file_name'] = file_name
            failed_files.append(error)
        else:
            processed_files.append(file_name)
        finally:
            if file is not None:
                file.close()


def is_existent_project(project_id):
    if not project_id.strip():
        return False
    return os.path.isdir(get_project_path(project_id))

def get_project_path(project_id):
    return '{}/{}'.format(PROJECTS_DIRECTORY, project_id)

def resolve_project(project_id_param):
    project_id = 'default'
    if project_id_param is not None:
        project_id = project_id_param
    return project_id

def check_process(process_file, project_id):
    tmp = os.popen('ps -Af | grep -w {}'.format(project_id)).read()
    proccount = tmp.count(process_file)

    if proccount > 0:
        raise Exception("Processing files for project_id '{}'. Try later!".format(project_id))

if __name__ == '__main__':
    if DEV_MODE == 1:
        LOGGER.info('Stating in DEV_MODE')
        app.run(host=HOST, port=PORT)
    else:
        waitress.serve(app, threads=THREADS, host=HOST, port=PORT, url_scheme=URL_SCHEME)
