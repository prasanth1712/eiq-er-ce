from polylogyx.models import db, User, Role, PlatformActivity, Node, Rule, Tag, Query, Pack, Settings, \
    ThreatIntelCredentials, VirusTotalAvEngines, Config, DefaultQuery, CarveSession, IOCIntel
from sqlalchemy import desc, and_, or_
import sqlalchemy


def add_user(**payload):
    if get_user(payload['username']):
        return False, 'User with this username already exists!'
    if get_user_by_email(payload['email']):
        return False, 'User with this mail id already exists!'
    try:
        return True, User.create(**payload)
    except sqlalchemy.exc.DataError:
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
    return User.query.filter(or_(User.username == username, User.email == username)).first()


def get_all_users(start, limit, search_term):
    total_count = User.query.count()
    qs = User.query
    if search_term:
        qs = qs.filter(or_(
            User.username.ilike('%' + search_term + '%'),
            User.email.ilike('%' + search_term + '%'),
            User.first_name.ilike('%' + search_term + '%'),
            User.last_name.ilike('%' + search_term + '%')
        ))
    if search_term:
        count = qs.count()
    else:
        count = total_count
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
    if username:
        if not User.query.filter(and_(User.username == username, User.id != user.id)).first():
            try:
                user.update(username=username)
            except sqlalchemy.exc.DataError:
                return False, "Username cannot exceed 80 characters!"
        else:
            return False, "This username is being used already by another user!"
    if email:
        if not User.query.filter(and_(User.email == email, User.id != user.id)).first():
            user.update(email=email, reset_email=False)
        else:
            return False, "This email is being used already by another user!"
    if first_name:
        user.update(first_name=first_name)
    if last_name:
        user.update(last_name=last_name)
    if role:
        user.update(roles=[role])
    if status is not None:
        user.update(status=status)
    if enable_sso is not None:
        user.update(enable_sso=enable_sso)
    return True, user


def get_users_activity(user_id, start, limit, searchterm):
    query_set = db.session.query(PlatformActivity)
    total_count = query_set.count()
    count = total_count
    count_again = False
    if user_id:
        query_set = query_set.filter(PlatformActivity.user_id == user_id)
        count_again = True
    if searchterm:
        user_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.user_id == User.id)\
            .filter(or_(User.username.ilike('%' + searchterm + '%'),
                        User.first_name.ilike('%' + searchterm + '%'),
                        User.last_name.ilike('%' + searchterm + '%')))
        node_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.node_id == Node.id)\
            .filter(or_(Node.node_info['computer_name'].astext.ilike('%' + searchterm + '%'),
                        Node.node_info['display_name'].astext.ilike('%' + searchterm + '%'),
                        Node.node_info['hostname'].astext.ilike('%' + searchterm + '%')))
        rule_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.rule_id == Rule.id)\
            .filter(Rule.name.ilike('%' + searchterm + '%'))
        tag_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.tag_id == Tag.id)\
            .filter(Tag.value.ilike('%' + searchterm + '%'))
        query_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.query_id == Query.id)\
            .filter(Query.name.ilike('%' + searchterm + '%'))
        pack_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.pack_id == Pack.id)\
            .filter(Pack.name.ilike('%' + searchterm + '%'))
        config_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.config_id == Config.id)\
            .filter(Config.name.ilike('%' + searchterm + '%'))
        settings_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.settings_id == Settings.id)\
            .filter(Settings.name.ilike('%' + searchterm + '%'))
        default_query_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.default_query_id == DefaultQuery.id)\
            .filter(DefaultQuery.name.ilike('%' + searchterm + '%'))
        threat_intel_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.threat_intel_credentials_id == ThreatIntelCredentials.id)\
            .filter(ThreatIntelCredentials.intel_name.ilike('%' + searchterm + '%'))
        vt_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.virus_total_av_engines_id == VirusTotalAvEngines.id)\
            .filter(VirusTotalAvEngines.name.ilike('%' + searchterm + '%'))
        ioc_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.ioc_intel_id == IOCIntel.id)\
            .filter(IOCIntel.threat_name.ilike('%' + searchterm + '%'))
        carve_qs = db.session.query(PlatformActivity.id).filter(PlatformActivity.carve_session_id == CarveSession.id)\
            .filter(CarveSession.session_id.ilike('%' + searchterm + '%'))
        qs_list = [user_qs, node_qs, rule_qs, tag_qs, query_qs, pack_qs, config_qs, settings_qs, default_query_qs,
                   threat_intel_qs, vt_qs, ioc_qs, carve_qs]
        qs_new = qs_list[0]
        query_set = query_set.filter(PlatformActivity.id.in_(qs_new.union_all(*qs_list).all()))
        count_again = True
    if count_again:
        count = query_set.count()
    results = query_set.order_by(desc(PlatformActivity.id)).offset(start).limit(limit).all()
    db.session.commit()
    return count, total_count, results
