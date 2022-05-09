from flask_restplus import Namespace, Resource, inputs
from flask import request, abort

from polylogyx.models import HandlingToken
from polylogyx.extensions import bcrypt
from polylogyx.blueprints.v1.utils import *
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.dao.v1 import users_dao
from polylogyx.authorize import admin_required, is_current_user_an_admin, MyUnauthorizedException
from polylogyx.utils import is_password_strong


ns = Namespace('users', description='User management')


@ns.route('', endpoint='users resource')
class Users(Resource):
    """
        Users resource
    """
    parser = requestparse(['username', 'email', 'password', 'first_name', 'last_name', 'role', 'enable_sso'],
                          [str, inputs.email(), str, str, str, str, inputs.boolean],
                          ['username', 'email', 'password', 'first_name', 'last_name', 'role', 'enable sso'],
                          [True, True, True, False, False, True, False],
                          [None, None, None, None, None, None, None],
                          [None, None, None, None, None, None, False])
    put_parser = requestparse(['username', 'role'], [list, str], ['username', 'role'], [True, True],
                              [None, None], [None, None])
    get_parser = requestparse(['start', 'limit', 'searchterm'], [int, int, str], ['start', 'limit', 'searchterm'],
                              [False, False, False], [None, None, None], [0, 10, None])

    @admin_required
    @ns.expect(get_parser)
    def get(self):
        """
            Returns all users list when the current user is authorized
        """
        args = self.get_parser.parse_args()
        users_qs = users_dao.get_all_users(args['start'], args['limit'], args['searchterm'])
        users = [user.to_dict() for user in users_qs[0]]
        message = "All users information has been fetched successfully"
        status = 'success'
        return marshal(prepare_response(message, status, {"results": users, "count": users_qs[1], "total_count": users_qs[2]}), parent_wrappers.common_response_wrapper)

    @admin_required
    @ns.expect(parser)
    def post(self):
        """
            Creates new users with the details given, Only users with admin access will be able to do this operation
        """
        args = self.parser.parse_args()
        status = "failure"
        existing_user = users_dao.get_user(args['username'])
        role = users_dao.get_role(args['role'])
        if not is_password_strong(args['password']):
            message = "Password should contain 1 uppercase, 1 lowercase, 1 digit, 1 special character and min 8 characters of length!"
        elif existing_user:
            message = "User with the username '{}' already exists!".format(args['username'])
        elif not role:
            message = "Role with the name '{}' does not exists!".format(args['role'])
        else:
            args['roles'] = [role]
            args['groups'] = []
            args['reset_password'] = True
            user = users_dao.add_user(**args)
            if user[0]:
                users_dao.assign_role(user[1], role)
                message = "User '{}' has been created successfully".format(user[1].username)
                status = 'success'
            else:
                status = 'failure'
                message = user[1]
        current_app.logger.info(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)

    @admin_required
    @ns.expect(put_parser)
    def put(self):
        """
            Assigns roles to users in bulk
            Just allows role assignment but not the information update
        """
        args = self.put_parser.parse_args()
        status = "failure"
        existing_users = users_dao.get_all_users_with_user_names_but_not_himself(args['username'])
        role = users_dao.get_role(args['role'])
        if not existing_users:
            message = "At least one correct user is needed for role assignment!"
        elif not role:
            message = "Role with the name '{}' does not exists!".format(args['role'])
        else:
            users_dao.bulk_user_role_assign(existing_users, role)
            message = "Users have been assigned with role '{}' successfully".format(role)
            status = 'success'
        current_app.logger.warning(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/me', endpoint='self user resource')
@ns.route('/user/<int:id>', endpoint='user resource')
class User(Resource):
    """
        User's resource
        Allowed for admin or self either
    """
    put_parser = requestparse(['email', 'new_user_name', 'first_name', 'last_name', 'role', 'status', 'enable_sso'],
                              [inputs.email(), str, str, str, str, inputs.boolean, inputs.boolean],
                              ['email', 'new_user_name', 'first_name', 'last_name', 'role', 'status', 'enable_sso'],
                              [False, False, False, False, False, False, False],
                              [None, None, None, None, None, None, None],
                              [None, None, None, None, None, None, None])
    get_parser = requestparse([], [], [], [])

    @ns.expect(get_parser)
    def get(self, id=None):
        """
            Get information of a user, to do this operation logged-in user should be fetching his information or
            logged-in user should have admin access
        """
        args = self.get_parser.parse_args()
        status = 'failure'
        data = None
        if id and is_current_user_an_admin():
            # Allowing admin
            user = users_dao.get_user_by_id(id)
        elif id:
            user = None
            abort(MyUnauthorizedException.code, MyUnauthorizedException.description)
        else:
            # Allowing user him self
            user = users_dao.get_current_user()
        if user:
            data = user.to_dict()
            message = "User '{}' information has been fetched successfully".format(user)
            status = 'success'
        else:
            message = "Could not find a user with id '{}'!".format(id)
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)

    @ns.expect(put_parser)
    def put(self, id=None):
        """
            Update a user information, to do this operation logged-in user should be updating his information or
            logged-in user should have admin access
        """
        args = self.put_parser.parse_args()
        status = "failure"
        role = None
        if id and is_current_user_an_admin():
            # Allowing admin
            user = users_dao.get_user_by_id(id)
        elif id:
            user = None
            abort(MyUnauthorizedException.code, MyUnauthorizedException.description)
        else:
            # Allowing user him self
            user = users_dao.get_current_user()
        if args['role']:
            role = users_dao.get_role(args['role'])
        if not user:
            message = "Could not find a user with id '{}'!".format(id)
        elif args['role'] and not role:
            message = "Role with the name '{}' does not exists!".format(args['role'])
        else:
            if is_current_user_an_admin() and not users_dao.is_current_user(user):
                result = users_dao.update_user(user, email=args['email'], first_name=args['first_name'],
                                               last_name=args['last_name'], role=role, username=args['new_user_name'],
                                               status=args['status'], enable_sso=args['enable_sso'])
            elif is_current_user_an_admin() and users_dao.is_current_user(user):
                result = users_dao.update_user(user, email=args['email'], first_name=args['first_name'],
                                               last_name=args['last_name'], username=args['new_user_name'],
                                               enable_sso=args['enable_sso'])
            elif users_dao.is_current_user(user):
                result = users_dao.update_user(user, first_name=args['first_name'], last_name=args['last_name'],
                                               username=args['new_user_name'])
            else:
                abort(MyUnauthorizedException.code, MyUnauthorizedException.description)
            if result[0]:
                message = "User's info has been updated successfully"
                status = 'success'
            else:
                message = result[1]
        current_app.logger.info(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/user/<int:id>/password', endpoint='user change password')
class ChangeUserPassword(Resource):
    """
        Place for admin to change other user's password
    """
    parser = requestparse(['new_password'], [str], ["new password"], [True])

    @admin_required
    @ns.expect(parser)
    def put(self, id):
        args = self.parser.parse_args()
        user = users_dao.get_user_by_id(id)
        status = "failure"
        if user:
            if is_password_strong(args['new_password']):
                user.update(password=bcrypt.generate_password_hash(args['new_password']
                                                                   .encode("utf-8")).decode("utf-8"), reset_password=True)
                for token_object in HandlingToken.query.filter(HandlingToken.token_expired == False)\
                        .filter(HandlingToken.user == user.username):
                    token_object.logged_out_at = dt.datetime.utcnow()
                    token_object.token_expired = True
                db.session.commit()
                message = "Password is updated successfully"
                status = "success"
            else:
                message = "Password should contain 1 uppercase, 1 lowercase, 1 digit, 1 special character and min 8 characters of length!"
        else:
            message = "No user exists with this id!"
        current_app.logger.info(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/me/password', endpoint='change password self')
class ChangeSelfPassword(Resource):
    """
        Changes user's password
    """
    parser = requestparse(['old_password', 'new_password', 'confirm_new_password'], [str, str, str],
                          ["old password", "new password", "confirm new password"], [True, True, True])

    @ns.expect(parser)
    def put(self):
        args = self.parser.parse_args()
        status = "failure"
        user = users_dao.get_current_user()
        if is_password_strong(args['new_password']):
            if bcrypt.check_password_hash(user.password, args['old_password']):
                # Verifying old password
                if not bcrypt.check_password_hash(user.password, args['new_password']):
                    # Verifying to not to allow the existing password to use
                    if args['new_password'] == args['confirm_new_password']:
                        current_app.logger.info("%s has changed the password", user.username)
                        user.update(password=bcrypt.generate_password_hash(args['new_password']
                                                                           .encode("utf-8")).decode("utf-8"),
                                    reset_password=False)
                        user_logged_in = HandlingToken.query.filter(
                           HandlingToken.token == request.headers.environ.get('HTTP_X_ACCESS_TOKEN')).first()

                        for token_object in HandlingToken.query.filter(HandlingToken.token_expired == False)\
                                .filter(HandlingToken.user == user_logged_in.user):
                            token_object.logged_out_at = dt.datetime.utcnow()
                            token_object.token_expired = True
                        db.session.commit()
                        message = "Password is updated successfully"
                        status = "success"
                    else:
                        message = "New password and confirm new password are not matching for the user"
                else:
                    message = "New password and old password should not be same"
            else:
                message = "Old password is not matching"
        else:
            message = "Password should contain 1 uppercase, 1 lowercase, 1 digit, 1 special character and min 8 characters of length!"
        current_app.logger.info(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/platform_activity', endpoint='Platform Activity')
class UserPlatformActivity(Resource):
    """
        User's platform activity
        Allowed for admin
    """
    parser = requestparse(['start', 'limit', 'user_id', 'searchterm'], [int, int, int, str],
                          ['start', 'limit', 'user_id', 'searchterm'], [False, False, False, False],
                          [None, None, None, None], [0, 25, None, None])

    @ns.expect(parser)
    def get(self):
        """
            Get platform activity of a user, to do this operation logged-in user should have admin access
        """
        args = self.parser.parse_args()
        results = []
        activity_qs = users_dao.get_users_activity(args['user_id'], args['start'], args['limit'], args['searchterm'])
        count = activity_qs[0]
        total_count = activity_qs[1]
        results_set = activity_qs[2]
        for item in results_set:
            result = {
                'id': item.id,
                'action': item.action,
                'text': item.text,
                'user': {
                    "id": item.user.id,
                    "first_name": item.user.first_name,
                    "last_name": item.user.last_name,
                    "username": item.user.username
                },
                'created_at': str(item.created_at)
            }
            if item.rule:
                result['item'] = {'type': "Rule", 'id': item.rule.id, 'name': item.rule.name}
            elif item.alert:
                result['item'] = {'type': "Alerts", 'id': item.alert.id}
            elif item.node:
                result['item'] = {'type': "Node", 'id': item.node.id, 'host_identifier': item.node.host_identifier,
                                  'name': item.node.display_name}
            elif item.carve_session:
                result['item'] = {'type': "CarveSession", 'id': item.carve_session.id,
                                  'session_id': item.carve_session.session_id}
            elif item.tag:
                result['item'] = {'type': "Tag", 'id': item.tag.id, 'name': item.tag.value}
            elif item.query:
                result['item'] = {'type': "Query", 'id': item.query.id, 'name': item.query.name}
            elif item.pack:
                result['item'] = {'type': "Pack", 'id': item.pack.id, 'name': item.pack.name}
            elif item.config:
                result['item'] = {'type': "Config", 'id': item.config.id, 'name': item.config.name,
                                  'platform': item.config.platform}
            elif item.settings:
                result['item'] = {'type': "Settings", 'id': item.settings.id, 'name': item.settings.name}
            elif item.default_filters:
                result['item'] = {'type': "DefaultFilters", 'id': item.default_filters.id,
                                  'config_id': item.default_filters.config.id,
                                  'config_name': item.default_filters.config.name,
                                  'platform': item.default_filters.config.platform
                                  }
            elif item.default_query:
                result['item'] = {'type': "DefaultQuery", 'id': item.default_query.id,
                                  'config_id': item.default_query.config.id,
                                  'config_name': item.default_query.config.name,
                                  'platform': item.default_query.config.platform
                                  }
            elif item.node_config:
                result['item'] = {'type': "NodeConfig", 'id': item.node_config.id,
                                  'node_id': item.node_config.node.id,
                                  'hostname': item.node_config.node.display_name}
            elif item.threat_intel_credentials:
                result['item'] = {'type': "ThreatIntelCredentials", 'id': item.threat_intel_credentials.id,
                                  'name': item.threat_intel_credentials.intel_name}
            elif item.ioc_intel:
                result['item'] = {'type': "IOCIntel", 'id': item.ioc_intel.id,
                                  'name': item.ioc_intel.threat_name}
            elif item.virus_total_av_engines:
                result['item'] = {'type': "VirusTotalAvEngines", 'id': item.virus_total_av_engines.id,
                                  'name': item.virus_total_av_engines.name}
            results.append(result)
        return marshal(prepare_response("Successfully fetched the latest user(s) platform activity", "success",
                                        {'count': count, 'total_count': total_count, 'results': results}),
                       parent_wrappers.common_response_wrapper, skip_none=True)
