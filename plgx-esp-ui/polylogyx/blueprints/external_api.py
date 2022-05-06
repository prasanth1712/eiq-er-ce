# -*- coding: utf-8 -*-
import jwt, werkzeug

from flask import abort, Blueprint, current_app, request, g
from flask.json import jsonify
from flask_restplus import Api

from polylogyx.models import User, HandlingToken
from polylogyx.blueprints import (nodes,distributed,configs,tags,alerts,packs,queries,schema,rules,carves,yara,iocs,common,email)
from polylogyx.utils import require_api_key
from .utils import *

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()


blueprint = Blueprint('external_api', __name__)
api = Api(blueprint,
    title='My Title',
    version='1.0',
    description='A description',
    decorators=[require_api_key],
)

#adds namespaces to the api
api.add_namespace(nodes.ns)
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
api.add_namespace(email.ns)


def validate_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.data:
            response = {}
            response['status'] = 'failure'
            response['message'] = 'Data missing'
            return jsonify(response)
        else:
            try:
                request.data = json.loads(request.data)
                return f(*args, **kwargs)
            except:
                current_app.logger.error("%s - Invalid data", request.remote_addr)
                abort(400)

        return f(*args, **kwargs)

    return decorated_function


@blueprint.route('/api')
def index():
    return '', 204


@blueprint.route('/login', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()

    # store token details into HandlingToken table
    payload = jwt.decode(token, current_app.config['SECRET_KEY'])
    user = User.query.filter_by(id=payload['id']).first()
    HandlingToken.create(token = token.decode("utf-8"), logged_in_at = dt.datetime.utcnow(), logged_out_at = None, user = user.username, token_expired = False)
    return jsonify({ 'token': token.decode('ascii')})


@require_api_key
@blueprint.route('/logout', methods=['POST'])
def logout_method():
    # store logout time and token_expired into InvalidateToken table
    user_logged_in = HandlingToken.query.filter(HandlingToken.token == request.headers.environ.get('HTTP_X_ACCESS_TOKEN')).first()
    if user_logged_in:
        user_logged_in.update(logged_out_at=dt.datetime.utcnow(), token_expired=True)
        return jsonify({'message': "user logged out successfully", 'status': "success"})
    return jsonify({'message': "API key passed is invalid", 'status': "failure"})


@auth.verify_password
def verify_password(username, password):
    try:
        request_json = json.loads(request.data)
    except json.decoder.JSONDecodeError:
        return abort(400, {'message': 'JSON Decode Error!'})
    print (request_json)
    if not ('username' in request_json and 'password' in request_json):
        return abort(400, {'message': 'Username and/or Password is/are missing!'})
    user = User.query.filter_by(username = request_json.get('username')).first()
    if not user or not user.check_password(request_json.get('password')):
        raise werkzeug.exceptions.Unauthorized
    g.user = user
    return True


@require_api_key
@blueprint.route('/swagger-doc', methods=['GET'])
def api_swagger_doc():
    return json.dumps(api.__schema__)
