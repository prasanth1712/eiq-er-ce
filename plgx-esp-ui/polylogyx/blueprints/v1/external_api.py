# -*- coding: utf-8 -*-
import jwt
import werkzeug
import json
import requests
from functools import wraps
from sqlalchemy import or_

from flask import Blueprint, g, request, abort, redirect, render_template
from flask.json import jsonify
from flask_restplus import Api
from flask_httpauth import HTTPBasicAuth

from polylogyx.models import User, HandlingToken, Role
from polylogyx.utils import require_api_key
from polylogyx.blueprints.v1.utils import *

auth = HTTPBasicAuth()


blueprint = Blueprint('external_api_v1', __name__)
api = Api(blueprint, title='My Title', version='1.0', description='A description', 
        decorators=[require_api_key]
        )

from polylogyx.blueprints.v1 import distributed, carves, queries, iocs, management, tags, dashboard, yara, rules, \
    common, configs, hosts, packs, schema, alerts, email, users


api.add_namespace(hosts.ns)
api.add_namespace(tags.ns)
api.add_namespace(configs.ns)
api.add_namespace(alerts.ns)
api.add_namespace(packs.ns)
api.add_namespace(queries.ns)
api.add_namespace(schema.ns)
api.add_namespace(rules.ns)
api.add_namespace(carves.ns)
api.add_namespace(yara.ns)
api.add_namespace(iocs.ns)
api.add_namespace(common.ns)
api.add_namespace(distributed.ns)
api.add_namespace(management.ns)
api.add_namespace(email.ns)
api.add_namespace(dashboard.ns)
api.add_namespace(users.ns)


def validate_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.data:
            return jsonify({'status': 'failure', 'message': 'Data missing'})
        else:
            try:
                request.data = json.loads(request.data)
                return f(*args, **kwargs)
            except Exception as e:
                current_app.logger.error("%s - Invalid data - %s", request.remote_addr, str(e))
                abort(400, jsonify({'status': "failure", "message": "Unknown error - {}".format(str(e))}))
        return f(*args, **kwargs)
    return decorated_function


@blueprint.route('/index', methods=['GET'])
def index():
    from polylogyx.dao.v1 import settings_dao
    # Returns the metadata about Authentication
    status = False
    sso_status = settings_dao.get_settings_by_name('sso_enable')
    if sso_status and sso_status.setting == 'true':
        status = True
    return jsonify({'sso_status': status})


@blueprint.route('/login', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    # Stores token details into HandlingToken table
    payload = jwt.decode(token, current_app.config['SECRET_KEY'])
    user = User.query.filter_by(id=payload['id']).first()
    all_roles = Role.query.all()
    HandlingToken.create(token=token.decode("utf-8"), logged_in_at=dt.datetime.utcnow(), logged_out_at=None,
                         user=user.username, token_expired=False)
    return jsonify({'first_name': user.first_name, 'last_name': user.last_name, 'token': token.decode('ascii'),
                    'reset_password': user.reset_password, 'reset_email': user.reset_email,
                    'roles': ','.join([role.name for role in user.roles]),
                    'all_roles': ','.join([role.name for role in all_roles]), 'auth_type': 'password'})


def generate_access_token():
    token = g.user.generate_auth_token()
    # Stores token details into HandlingToken table
    payload = jwt.decode(token, current_app.config['SECRET_KEY'])
    user = User.query.filter_by(id=payload['id']).first()
    all_roles = Role.query.all()
    HandlingToken.create(token=token.decode("utf-8"), logged_in_at=dt.datetime.utcnow(), logged_out_at=None,
                         user=user.username, token_expired=False)
    return {'first_name': user.first_name, 'last_name': user.last_name, 'token': token.decode('ascii'),
            'roles': ','.join([role.name for role in user.roles]),
            'all_roles': ','.join([role.name for role in all_roles])}


@require_api_key
@blueprint.route('/logout', methods=['POST'])
def logout_method():
    # Stores the logout time and token_expired into InvalidateToken table
    user_logged_in = HandlingToken.query\
        .filter(HandlingToken.token == request.headers.environ.get('HTTP_X_ACCESS_TOKEN')).first()
    if user_logged_in:
        user_logged_in.update(logged_out_at=dt.datetime.utcnow(), token_expired=True)
        return jsonify({'message': "user logged out successfully", 'status': "success"})
    current_app.logger.error("API key passed is invalid!")
    return jsonify({'message': "API key passed is invalid!", 'status': "failure"})


@auth.verify_password
def verify_password(username, password):
    """
    Method to verify the user's password
    Returns True if password of the user is valid
    """
    try:
        request_json = json.loads(request.data)
    except json.decoder.JSONDecodeError:
        current_app.logger.error('JSON Decode Error!')
        return abort(400, jsonify({'message': 'JSON Decode Error!'}))
    if not ('username' in request_json and 'password' in request_json):
        current_app.logger.error('Username and/or Password is/are missing!')
        return abort(400, jsonify({'message': 'Username and/or Password is/are missing!'}))
    user = User.query.filter(or_(User.username == request_json.get('username'),
                                 User.email == request_json.get('username'))).filter(User.status != False).first()
    if not user or not user.check_password(request_json.get('password')):
        raise werkzeug.exceptions.Unauthorized
    g.user = user
    return True


# SAML Section

def get_saml_acs_and_redirect_url():
    from polylogyx.utils import get_server_ip
    from polylogyx.settings import ProdConfig
    if current_app.config['ENV'] == ProdConfig.ENV:
        ip = get_server_ip()
        current_app.logger.info("IP detected from flags file is -- {}".format(ip))
        acs = 'https://{}/esp-ui/services/api/v1/sso/callback'.format(ip)
        dashboard_url = 'https://{}/dashboard'.format(ip)
        login_url = 'https://{}/authentication/login'.format(ip)
    else:
        acs = 'https://localhost:5000/services/api/v1/sso/callback'
        dashboard_url = 'http://localhost:4200/dashboard'
        login_url = 'http://localhost:4200/authentication/login'
    return acs, dashboard_url, login_url


def get_saml_client():
    """
        The configuration is a hash for use by saml2.config.Config
    """

    from saml2 import (BINDING_HTTP_POST, BINDING_HTTP_REDIRECT)
    from saml2.client import Saml2Client
    from saml2.config import Config as Saml2Config
    from polylogyx.dao.v1.settings_dao import get_sso_configuration

    acs_url, dashboard_url, login_url = get_saml_acs_and_redirect_url()
    saml_config = get_sso_configuration()
    if not saml_config:
        return
    try:
        rv = requests.get(saml_config['idp_metadata_url'])
    except Exception as e:
        message = "Bad SAML Configuration, Please correct it! -- {}".format(str(e))
        current_app.logger.error(message)
        return
    settings = {
        'name': saml_config['app_name'],
        'entityid': saml_config['entity_id'],
        'metadata': {'inline': [rv.text], },
        'service': {
            'sp': {
                'endpoints': {
                    'assertion_consumer_service': [(acs_url, BINDING_HTTP_REDIRECT), (acs_url, BINDING_HTTP_POST),
                                                   (acs_url, BINDING_HTTP_REDIRECT), (acs_url, BINDING_HTTP_POST)],
                },
                'allow_unsolicited': True,
                'authn_requests_signed': False,
                'logout_requests_signed': True,
                'want_assertions_signed': True,
                'want_response_signed': False,
            },
        },
    }
    sp_config = Saml2Config()
    try:
        sp_config.load(settings)
    except Exception as e:
        current_app.logger.error(str(e))
        return
    sp_config.allow_unknown_attributes = True
    saml_client = Saml2Client(config=sp_config)
    return saml_client


@blueprint.route('/sso/callback', endpoint='sso acs endpoint', methods=['POST'])
def assertion_consumer_service():
    """
        A JWT key which is a SAML Request response from IDP will be collected here
        SAML Response will be decoded here to get the username or email which again requires for our own user validation
        Returns a JWT access token along by redirecting it to dashboard page
    """
    from polylogyx.dao.v1 import users_dao
    from saml2 import entity

    acs_url, dashboard_url, login_url = get_saml_acs_and_redirect_url()
    saml_client = get_saml_client()
    if not saml_client:
        message = "SAML Configuration is empty/incorrect! Please update before proceeding..."
        current_app.logger.info(message)
        return render_template('ssoOnFailure.html', url_to_redirect=login_url, error_message=message)
    try:
        auth_n_response = saml_client.parse_authn_request_response(request.form['SAMLResponse'], entity.BINDING_HTTP_POST)
    except Exception as e:
        message = "SSO Configuration provided is not matching with the app defined in IDP! Please check!"
        current_app.logger.info(message)
        current_app.logger.info(str(e))
        return render_template('ssoOnFailure.html', url_to_redirect=login_url, error_message=message)
    auth_n_response.get_identity()
    user_info = auth_n_response.get_subject()
    username = user_info.text

    # Create a token here and send back to UI, may be a redirect
    _user = users_dao.get_user_by_mail_or_username(username)
    if not _user:
        message = "No user found for the username/email received from IDP!"
        current_app.logger.info(message)
        return render_template('ssoOnFailure.html', url_to_redirect=login_url, error_message=message)
    if not _user.enable_sso:
        message = "User has not been assigned to use SSO for the username/email received from IDP!"
        current_app.logger.info(message)
        return render_template('ssoOnFailure.html', url_to_redirect=login_url, error_message=message)
    g.user = _user
    app_auth_response = generate_access_token()
    if 'RelayState' in request.form and request.form['RelayState']:
        url_to_redirect = request.form['RelayState']
    else:
        url_to_redirect = dashboard_url
    return render_template('ssoOnSuccess.html', url_to_redirect=url_to_redirect,
                           first_name=app_auth_response['first_name'],
                           access_token=app_auth_response['token'],
                           roles=app_auth_response['roles'], all_roles=app_auth_response['all_roles'], auth_type='sso')


@blueprint.route('/sso/login', endpoint='sso login endpoint', methods=['GET'])
def sso_login():
    """
        Returns the SAML Request content, that to be made by our UI
        The Request content contains the SP information like certificate, EntityID, Redirection URL etc.,
    """
    from polylogyx.dao.v1.settings_dao import get_sso_enabled_status
    acs_url, dashboard_url, login_url = get_saml_acs_and_redirect_url()
    sso_status = get_sso_enabled_status()
    if sso_status is None or not sso_status:
        # Abort SSO Authentication
        message = "ER is not enabled for SSO, Please enable it!"
        current_app.logger.info(message)
        return render_template('ssoOnFailure.html', url_to_redirect=login_url, error_message=message)
    saml_client = get_saml_client()
    if not saml_client:
        message = "SAML Configuration is empty/incorrect! Please update before proceeding..."
        current_app.logger.info(message)
        return render_template('ssoOnFailure.html', url_to_redirect=login_url, error_message=message)
    req_id, info = saml_client.prepare_for_authenticate()
    saml_url = None
    for key, value in info['headers']:
        if key is 'Location':
            # On successful SSO SP config loading, request will be redirected to IDP SAML App
            saml_url = value
    response = redirect(saml_url, code=302)
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response

# SAML Section
