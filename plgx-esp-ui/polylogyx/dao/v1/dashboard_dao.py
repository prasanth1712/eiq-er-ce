from sqlalchemy import func, or_, and_, not_

from polylogyx.models import db, Node, Alerts, Rule
from polylogyx.constants import ModelStatusFilters


def get_platform_count():
    platform_count_list = []
    host_distribution = db.session.query(Node.platform, db.func.count(Node.id)).filter(ModelStatusFilters.HOSTS_NON_DELETED).group_by(Node.platform).all()
    for pair in host_distribution:
        platform_count_list.append({"os_name":pair[0], "count":pair[1]})
    return platform_count_list


def get_online_node_count(current_time):
    return db.session.query(db.func.count(Node.id)).filter(ModelStatusFilters.HOSTS_ENABLED).filter(or_(Node.is_active,
            Node.last_checkin > current_time)).scalar()


def get_offline_node_count(current_time):
    return db.session.query(db.func.count(Node.id)).filter(ModelStatusFilters.HOSTS_ENABLED).filter(and_(not_(Node.is_active),
            Node.last_checkin < current_time)).scalar()


def get_rules_data(limits):
    return db.session.query(Alerts.rule_id, Rule.name, func.count(Alerts.rule_id)).filter(
        Alerts.source == Alerts.RULE).join(Alerts.rule).join(Alerts.node).filter(ModelStatusFilters.HOSTS_NON_DELETED).filter(
        ModelStatusFilters.ALERTS_NON_RESOLVED).group_by(
        Alerts.rule_id, Rule.name).order_by(
        func.count(Alerts.rule_id).desc()).limit(limits).all()


def get_host_data(limits):
    return db.session.query(Alerts.node_id, Node.host_identifier, Node.node_info['computer_name'], func.count(
        Alerts.node_id)).join(Alerts.node).group_by(
        Alerts.node_id, Node.host_identifier, Node.node_info['computer_name']).filter(ModelStatusFilters.ALERTS_NON_RESOLVED).filter(ModelStatusFilters.HOSTS_NON_DELETED).order_by(
        func.count(Alerts.node_id).desc()).limit(limits).all()


def get_queries(limits):
    return db.session.query(Alerts.query_name, func.count(Alerts.query_name)).filter(
        ModelStatusFilters.ALERTS_NON_RESOLVED).join(Alerts.node).filter(ModelStatusFilters.HOSTS_NON_DELETED).group_by(
        Alerts.query_name).order_by(
        func.count(Alerts.query_name).desc()).limit(limits).all()


def get_alert_count():
    return db.session.query(Alerts.source, Alerts.severity, db.func.count(
        Alerts.severity)).filter(ModelStatusFilters.ALERTS_NON_RESOLVED).join(Alerts.node).filter(ModelStatusFilters.HOSTS_NON_DELETED).group_by(
        Alerts.source, Alerts.severity).all()
