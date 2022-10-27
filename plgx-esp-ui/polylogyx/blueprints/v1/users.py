from flask_restful import Resource, inputs
from flask import request, abort
from polylogyx.blueprints.v1.external_api import api
from polylogyx.models import AuthToken, User
from polylogyx.extensions import bcrypt
from polylogyx.blueprints.v1.utils import *
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.dao.v1 import users_dao
from polylogyx.authorize import admin_required, is_current_user_an_admin, MyUnauthorizedException
from polylogyx.utils import is_password_strong, is_username_valid
from polylogyx.db.signals import receive_after_update


@api.resource ('/users', endpoint='users resource')
class Users(Resource):
    """
        Users resource
    """
    parser = requestparse(['username', 'email', 'password', 'first_name', 'last_name', 'role', 'enable_sso'],
                          [str, is_email_valid, str, str, str, str, inputs.boolean],
                          ['username', 'email', 'password', 'first_name', 'last_name', 'role', 'enable sso'],
                          [True, True, True, True, False, True, False],
                          [None, None, None, None, None, None, None],
                          [None, None, None, None, None, None, False])
    put_parser = requestparse(['username', 'role'], [list, str], ['username', 'role'], [True, True],
                              [None, None], [None, None])
    get_parser = requestparse(['start', 'limit', 'searchterm','order_by','column','role','status'], [int, int, str,str,str,str,inputs.boolean], ['start', 'limit', 'searchterm','order_by','col','role','status'],
                              [False, False, False,False,False,False,False], [None, None, None,['ASC','asc','Asc','DESC','desc','Desc'],['username'],None,None], [0, 10, None,None,None,None,None])

    @admin_required
    def get(self):
        """
            Returns all users list when the current user is authorized
        """
        args = self.get_parser.parse_args()
        order_by=None
        if args['order_by'] in ['ASC','asc','Asc']:
            order_by='asc'
        elif args['order_by'] in ['DESC','desc','Desc']:
            order_by = 'desc'
        users_qs = users_dao.get_all_users(args['start'], args['limit'], args['searchterm'],args['column'],order_by,args['role'],args['status'])
        users = [user.to_dict() for user in users_qs[0]]
        message = "All users information has been fetched successfully"
        status = 'success'
        return marshal(prepare_response(message, status, {"results": users, "count": users_qs[1], "total_count": users_qs[2]}), parent_wrappers.common_response_wrapper)

    @admin_required
    def post(self):
        """
            Creates new users with the details given, Only users with admin access will be able to do this operation
        """
        args = self.parser.parse_args()
        args['username'] = args['username'].strip()
        status = "failure"
        existing_user = users_dao.get_user(args['username'])
        role = users_dao.get_role(args['role'])
        if (args['username'] is not None and not args['username']) or not is_username_valid(args['username']):
            message = f"Username should contain atleast one alphabet and should have length between {current_app.config.get('INI_CONFIG', {}).get('min_username_length', 3)} and {current_app.config.get('INI_CONFIG', {}).get('max_username_length', 64)}"
        elif not is_password_strong(args['password']):
            message = "Password should contain 1 uppercase, 1 lowercase, 1 digit, 1 special character and min 8 characters of length!"
        elif existing_user:
            message = "User with the username '{}' already exists!".format(args['username'])
        elif not role:
            message = "Role with the name '{}' does not exists!".format(args['role'])
        else:
            user = users_dao.add_user(args['username'], email=args['email'], password=args['password'], first_name=args['first_name'], last_name=args['last_name'], roles=[role], enable_sso=args['enable_sso'])
            if user[0]:
                message = "User '{}' has been created successfully".format(user[1].username)
                status = 'success'
            else:
                status = 'failure'
                message = user[1]
        current_app.logger.info(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)

    @admin_required
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
            for user in existing_users:
                receive_after_update(None, db.session, user)
            message = "Users have been assigned with role '{}' successfully".format(role)
            status = 'success'
        current_app.logger.warning(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource ('/users/me', endpoint='self user resource')
@api.resource ('/users/user/<int:id>', endpoint='user resource')
class UserResource(Resource):
    """
        User's resource
        Allowed for admin or self either
    """
    put_parser = requestparse(['email', 'new_user_name', 'first_name', 'last_name', 'role', 'status', 'enable_sso'],
                              [is_email_valid, str, str, str, str, inputs.boolean, inputs.boolean],
                              ['email', 'new_user_name', 'first_name', 'last_name', 'role', 'status', 'enable_sso'],
                              [False, False, False, False, False, False, False],
                              [None, None, None, None, None, None, None],
                              [None, None, None, None, None, None, None])
    get_parser = requestparse([], [], [], [])

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
        if args['new_user_name'] is not None and (not args['new_user_name'] or not is_username_valid(args['new_user_name'])):
            message = f"Username should contain atleast one alphabet and should have length between {current_app.config.get('INI_CONFIG', {}).get('min_username_length', 3)} and {current_app.config.get('INI_CONFIG', {}).get('max_username_length', 64)}"
        elif not user:
            message = "Could not find a user with id '{}'!".format(id)
        elif args['role'] and not role:
            message = "Role with the name '{}' does not exists!".format(args['role'])
        else:
            if args['new_user_name']:
                args['new_user_name'] = args['new_user_name'].strip()
            if is_current_user_an_admin() and not users_dao.is_current_user(user):
                result = users_dao.update_user(user, email=args['email'], first_name=args['first_name'],
                                               last_name=args['last_name'], role=role, username=args['new_user_name'],
                                               status=args['status'], enable_sso=args['enable_sso'])
            elif is_current_user_an_admin() and users_dao.is_current_user(user):
                user_dict = user.to_dict()
                if (args['status'] is not None and args['status'] != user_dict['status']) or (args['role'] and args['role'] not in user_dict['roles']):
                    message = "Current user will not able to change role or deactivate self"
                    return marshal(prepare_response(message,'failure'),parent_wrappers.failure_response_parent)
                else:
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
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource ('/users/user/<int:id>/password', endpoint='user change password')
class ChangeUserPassword(Resource):
    """
        Place for admin to change other user's password
    """
    parser = requestparse(['new_password'], [str], ["new password"], [True])

    @admin_required
    def put(self, id):
        args = self.parser.parse_args()
        user = users_dao.get_user_by_id(id)
        status = "failure"
        if user:
            if is_password_strong(args['new_password']):
                user.update(password=bcrypt.generate_password_hash(args['new_password']
                                                                   .encode("utf-8")).decode("utf-8"), reset_password=True)
                for token_object in AuthToken.query.filter(AuthToken.token_expired == False)\
                        .filter(AuthToken.user == user):
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
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource ('/users/me/password', endpoint='change password self')
class ChangeSelfPassword(Resource):
    """
        Changes user's password
    """
    parser = requestparse(['old_password', 'new_password', 'confirm_new_password'], [str, str, str],
                          ["old password", "new password", "confirm new password"], [True, True, True])

    
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
                        user_logged_in = AuthToken.query.filter(
                           AuthToken.token == request.headers.environ.get('HTTP_X_ACCESS_TOKEN')).first()

                        for token_object in AuthToken.query.filter(AuthToken.token_expired == False)\
                                .filter(AuthToken.user == user_logged_in.user):
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
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource ('/users/platform_activity', endpoint='Platform Activity')
class UserPlatformActivity(Resource):
    """
        User's platform activity
        Allowed for admin
    """
    parser = requestparse(['start', 'limit', 'user_id', 'searchterm'], [int, int, int, str],
                          ['start', 'limit', 'user_id', 'searchterm'], [False, False, False, False],
                          [None, None, None, None], [0, 25, None, None])
    @admin_required
    def get(self):
        """
            Get platform activity of a user, to do this operation logged-in user should have admin access
        """
        from polylogyx.models import Node, Rule, Tag, Query, Pack, Settings, \
            ThreatIntelCredentials, VirusTotalAvEngines, Config, DefaultQuery, CarveSession, IOCIntel, Alerts, \
            NodeConfig, DefaultFilters
        args = self.parser.parse_args()
        results = []
        entities_list = [Rule, Alerts, Node, CarveSession, Tag, Query, Pack, Config, Settings, DefaultFilters, \
                            DefaultQuery, NodeConfig, ThreatIntelCredentials, IOCIntel, User, VirusTotalAvEngines]
        activity_qs = users_dao.get_users_activity(args['user_id'], args['start'], args['limit'], args['searchterm'])
        count = activity_qs[0]
        total_count = activity_qs[1]
        results_set = activity_qs[2]
        for item in results_set:
            entity_found = False    # Using this flag to decide and compute the type of entity,
                                    # if incase the entity does bulk actions only like IOC update or Virus Total engines config update
            pa_obj = item[0]
            result = {
                'id': pa_obj.id,
                'action': pa_obj.action,
                'text': pa_obj.text,
                'user': {
                    "id": pa_obj.user.id,
                    "first_name": pa_obj.user.first_name,
                    "last_name": pa_obj.user.last_name,
                    "username": pa_obj.user.username
                },
                'created_at': str(pa_obj.created_at)
            }
            entity_dict = {}
            for entity in item[1:]:
                # Index 0 in item object is PlatformActivity object, So iterating from 1 to iterate over entity types only
                if entity:
                    # As things we are collecting are based on the type of entity and column name of the entity, 
                    # We are not able to get rid of these many if and else condition
                    entity_found = True
                    if getattr(entity, 'get_entity_dict') and entity.get_entity_dict() is not None:
                        entity_dict = entity.get_entity_dict()
                        
            if not entity_found and not entity_dict:
                # For all the entries for which join cannot happen because of their hard deletion in the db or those entries with out id, 
                # We just show their ids for all the entries of those objects so collecting only id here
                for table_kls in entities_list:
                    if pa_obj.entity == table_kls.__tablename__:
                        entity_dict = {
                            'type': table_kls.__name__
                        }
                        if pa_obj.entity_id:
                            entity_dict['id'] = pa_obj.entity_id
                        break
            result['item'] = entity_dict
            results.append(result)
        return marshal(prepare_response("Successfully fetched the latest user(s) platform activity", "success",
                                        {'count': count, 'total_count': total_count, 'results': results}),
                       parent_wrappers.common_response_wrapper)
