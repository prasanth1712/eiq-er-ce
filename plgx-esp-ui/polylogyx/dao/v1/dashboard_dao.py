from sqlalchemy import func, or_, and_, not_

from polylogyx.models import db, Node, DashboardData, Alerts, Rule


def get_platform_count():
    platform_count_list = []
    host_distribution = db.session.query(Node.platform, db.func.count(Node.id)).filter(and_(Node.state!=Node.DELETED, Node.state!=Node.REMOVED)).group_by(Node.platform).all()
    for pair in host_distribution:
        platform_count_list.append({"os_name":pair[0], "count":pair[1]})
    return platform_count_list


def get_online_node_count(current_time):
    return db.session.query(db.func.count(Node.id)).filter(and_(Node.state!=Node.DELETED, Node.state!=Node.REMOVED)).filter(or_(Node.is_active,
            Node.last_checkin > current_time)).scalar()


def get_offline_node_count(current_time):
    return db.session.query(db.func.count(Node.id)).filter(and_(Node.state!=Node.DELETED, Node.state!=Node.REMOVED)).filter(and_(not_(Node.is_active),
            Node.last_checkin < current_time)).scalar()


def get_rules_data(limits):
    return db.session.query(Alerts.rule_id, Rule.name, func.count(Alerts.rule_id)).filter(
        Alerts.source == Alerts.RULE).join(Alerts.rule).join(Alerts.node).filter(and_(Node.state!=Node.DELETED, Node.state!=Node.REMOVED)).filter(
        or_(Alerts.status == None, Alerts.status != Alerts.RESOLVED)).group_by(
        Alerts.rule_id, Rule.name).order_by(
        func.count(Alerts.rule_id).desc()).limit(limits).all()


def get_host_data(limits):
    return db.session.query(Alerts.node_id, Node.host_identifier, Node.node_info['computer_name'], func.count(
        Alerts.node_id)).join(Alerts.node).group_by(
        Alerts.node_id, Node.host_identifier, Node.node_info['computer_name']).filter(or_(
        Alerts.status == None, Alerts.status != Alerts.RESOLVED)).filter(and_(Node.state!=Node.DELETED, Node.state!=Node.REMOVED)).order_by(
        func.count(Alerts.node_id).desc()).limit(limits).all()


def get_querries(limits):
    return db.session.query(Alerts.query_name, func.count(Alerts.query_name)).filter(
        or_(Alerts.status == None, Alerts.status != Alerts.RESOLVED)).join(Alerts.node).filter(and_(Node.state!=Node.DELETED, Node.state!=Node.REMOVED)).group_by(
        Alerts.query_name).order_by(
        func.count(Alerts.query_name).desc()).limit(limits).all()


def get_alert_count():
    return db.session.query(Alerts.source, Alerts.severity, db.func.count(
        Alerts.severity)).filter(or_(
        Alerts.status == None, Alerts.status != Alerts.RESOLVED)).join(Alerts.node).filter(and_(Node.state!=Node.DELETED, Node.state!=Node.REMOVED)).group_by(
        Alerts.source, Alerts.severity).all()
