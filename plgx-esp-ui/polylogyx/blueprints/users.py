from flask import jsonify, request
from flask_restplus import Namespace, Resource, marshal
from flask_login import current_user
from polylogyx.utils import require_api_key
from .utils import *
from polylogyx.models import User
from polylogyx.wrappers import parent_wrappers as parentwrapper
from polylogyx.extensions import bcrypt
from polylogyx.models import ThreatIntelCredentials, HandlingToken

ns = Namespace('users', description='user info related operations')


@require_api_key
@ns.route('/changepw', endpoint='change_password')
@ns.doc(params = {'old_password':"old password", 'new_password':"new password", 'confirm_new_password':"confirm new password"})
class ChangePassword(Resource):
    """changes user password"""
    parser = requestparse(['old_password', 'new_password', 'confirm_new_password'], [str, str, str], ["old password", "new password", "confirm new password"])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        status = "failure"
        import jwt
        payload = jwt.decode(request.headers.environ.get('HTTP_X_ACCESS_TOKEN'), current_app.config['SECRET_KEY'])
        user = User.query.filter_by(id=payload['id']).first()
        if args['new_password']==args['confirm_new_password']:
            if bcrypt.check_password_hash(user.password, args['old_password']):
                #current_app.logger.info("%s has changed password and the old password and new passwords are %s and %s", username, args['old_password'], args['new_password'])
                #user.update(password=bcrypt.generate_password_hash(args['new_password']))
                user_logged_in = HandlingToken.query.filter(
                    HandlingToken.token == request.headers.environ.get('HTTP_X_ACCESS_TOKEN')).first()
                if user_logged_in:
                    user_logged_in.update(logged_out_at=dt.datetime.utcnow(), token_expired=True)
                message = "password is updated successfully"
                status = "success"
            else:
                message = "old password is not matching"
        else:
            message = "new password and confirm new password are not matching for the user"
        return marshal(prepare_response(message,status),parentwrapper.common_response_wrapper,skip_none=True)
