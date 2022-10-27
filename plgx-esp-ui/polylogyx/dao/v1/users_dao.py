from polylogyx.models import db, User, Role, PlatformActivity, Node, Rule, Tag, Query, Pack, Settings, \
    ThreatIntelCredentials, VirusTotalAvEngines, Config, DefaultQuery, CarveSession, IOCIntel, Alerts, NodeConfig, \
    DefaultFilters
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import aliased
import sqlalchemy


def add_user(username, email=None, password=None, first_name=None, last_name=None, roles=None, enable_sso=None):
    if get_user(username):
        return False, 'User with this username already exists!'
    if get_user_by_email(email):
        return False, 'User with this mail id already exists!'
    try:
        return True, User.create(username=username, email=email, password=password, first_name=first_name, last_name=last_name, roles=roles, groups=[], reset_password=True, enable_sso=enable_sso)
    except sqlalchemy.exc.DataError:
        # As column value length is set on the model, We use exception than a explicit check to check the length of it
        return False, "Username cannot exceed 80 characters!"


def get_current_user():
    from flask import g
    if hasattr(g, 'user') and g.user:
        return g.user
    return None


def is_current_user(user):
    if user == get_current_user():
        return True
    return False


def get_user(username):
    return User.query.filter(User.username == username).first()


def get_user_by_id(id):
    return User.query.filter(User.id == id).first()


def get_user_by_email(email):
    return User.query.filter(User.email == email).first()


def get_user_by_mail_or_username(username):
    return User.query.filter(or_(User.username == username, User.email == username)).filter(User.status != False).first()


def get_all_users(start, limit, search_term,col=None,order_by=None,role=None,status=None):
    total_count = User.query.count()
    qs = db.session.query(User)
    if role:
        role = get_role(role)
        qs = qs.filter(User.roles.any(Role.id == role.id))
    if status is not None:
        qs = qs.filter(User.status == status)
    if search_term:
        qs = qs.filter(or_(
            User.username.ilike('%' + search_term + '%'),
            User.email.ilike('%' + search_term + '%'),
            User.first_name.ilike('%' + search_term + '%'),
            User.last_name.ilike('%' + search_term + '%')
        ))
    if search_term or role or status is not None:
        count = qs.count()
    else:
        count = total_count
    if order_by and order_by == 'asc':
        qs=qs.order_by(User.username)
    if order_by and order_by == 'desc':
        qs=qs.order_by(desc(User.username))
    if start is not None and limit:
        qs = qs.offset(start).limit(limit)
    return qs.all(), count, total_count


def get_all_roles():
    return [role.name for role in Role.query.all()]


def get_admin_role():
    return Role.query.order_by(desc(Role.access_level)).first()


def get_all_users_with_user_names_but_not_himself(usernames):
    return User.query.filter(and_(User.username.in_(usernames), User.id != get_current_user().id)).all()


def get_role(role):
    return Role.query.filter(Role.name == role).first()


def assign_role(user, role):
    user.update(roles=[role])


def bulk_user_role_assign(users, role):
    for user in users:
        user.roles = [role]
    db.session.commit()


def bulk_user_deletion(users):
    for user in users:
        user.roles = []
        user.delete()
    db.session.commit()


def delete_user(user):
    return user.delete()


def update_user(user, email=None, first_name=None, last_name=None, role=None, username=None, status=None,
                enable_sso=None):
    dict_to_update = {}
    if username:
        if not User.query.filter(and_(User.username == username, User.id != user.id)).first():
            try:
                dict_to_update['username'] = username
            except sqlalchemy.exc.DataError:
                # As column value length is set on the model, We use exception than a explicit check to check the length of it
                return False, "Username cannot exceed 80 characters!"
        else:
            return False, "This username is being used already by another user!"
    if email:
        if not User.query.filter(and_(User.email == email, User.id != user.id)).first():
            dict_to_update['email'] = email
            dict_to_update['reset_email'] = False
            # reset_email will be set to true only to those users who gets added as part of server initial compose
        else:
            return False, "This email is being used already by another user!"
    if first_name:
        dict_to_update['first_name'] = first_name
    if last_name is not None:
        dict_to_update['last_name'] = last_name
    if role:
        dict_to_update['roles'] = [role]
        # As role column in a many to many relationship, We should give it in a list
    if status is not None:
        dict_to_update['status'] = status
        # Setting this controls user to the platform, Setting True allows user to login and False restricts
    if enable_sso is not None:
        dict_to_update['enable_sso'] = enable_sso
        # Setting this will allow user to use SSO login
    user.update(**dict_to_update)
    return True, user


def get_users_activity(user_id, start, limit, searchterm):
    AliasedUser = aliased(User)
    # As user is being joined for owner column, We needed to aliase and join
    to_join = [Node, Rule, Alerts, Tag, Query, Pack, Config, Settings, DefaultFilters, DefaultQuery, NodeConfig,
               ThreatIntelCredentials, VirusTotalAvEngines, IOCIntel, CarveSession, AliasedUser]

    query_set = db.session.query(PlatformActivity, Node, Rule, Alerts, Tag, Query, Pack, Config, Settings,
                                 DefaultFilters, DefaultQuery, NodeConfig, ThreatIntelCredentials, VirusTotalAvEngines,
                                 IOCIntel, CarveSession, AliasedUser).join(User, PlatformActivity.user_id == User.id)
    for table_kls in to_join:
        # All the models which records the user activity are added to be joined with outer join
        query_set = query_set.outerjoin(table_kls, and_(PlatformActivity.entity_id == table_kls.id,
                                                        PlatformActivity.entity == table_kls.__tablename__))

    total_count = query_set.count()
    count = total_count
    count_again = False  
    # Using this flag to decide if the count query needs to run again, Will be True only when a searchterm is passed

    if user_id:
        query_set = query_set.filter(PlatformActivity.user_id == user_id)
        count_again = True

    if searchterm:
        query_set = query_set.filter(or_(
                                        User.username.ilike('%' + searchterm + '%'),
                                        User.first_name.ilike('%' + searchterm + '%'),
                                        User.last_name.ilike('%' + searchterm + '%'),
                                        Node.node_info['computer_name'].astext.ilike('%' + searchterm + '%'),
                                        Node.node_info['display_name'].astext.ilike('%' + searchterm + '%'),
                                        Node.node_info['hostname'].astext.ilike('%' + searchterm + '%'),
                                        Rule.name.ilike('%' + searchterm + '%'),
                                        Tag.value.ilike('%' + searchterm + '%'),
                                        Query.name.ilike('%' + searchterm + '%'),
                                        Pack.name.ilike('%' + searchterm + '%'),
                                        Config.name.ilike('%' + searchterm + '%'),
                                        Config.platform.ilike('%' + searchterm + '%'),
                                        Settings.name.ilike('%' + searchterm + '%'),
                                        DefaultQuery.name.ilike('%' + searchterm + '%'),
                                        ThreatIntelCredentials.intel_name.ilike('%' + searchterm + '%'),
                                        VirusTotalAvEngines.name.ilike('%' + searchterm + '%'),
                                        IOCIntel.threat_name.ilike('%' + searchterm + '%'),
                                        CarveSession.session_id.ilike('%' + searchterm + '%')))
        count_again = True

    if count_again:
        count = query_set.count()

    results = query_set.order_by(desc(PlatformActivity.created_at)).offset(start).limit(limit).all()

    return count, total_count, results
