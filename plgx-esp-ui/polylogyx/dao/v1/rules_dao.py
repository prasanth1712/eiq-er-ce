from polylogyx.models import Rule, Alerts, db, Node
from sqlalchemy import desc, or_, and_, asc


def get_rule_by_id(rule_id):
    return Rule.query.filter(Rule.id == rule_id).first()


def get_rule_name_by_id(rule_id):
    rule=Rule.query.filter(Rule.id == rule_id).first()
    return rule.name


def get_rule_alerts_count():
    return db.session.query(Alerts).filter(Alerts.source==Alerts.RULE).filter(
        or_(Alerts.status == None, Alerts.status != Alerts.RESOLVED)).filter(and_(Node.state != Node.REMOVED, Node.state != Node.DELETED)).join(Node,
        Alerts.node_id == Node.id).count()


def get_all_rules(searchterm='', alerts_count=False):
    if alerts_count:
        removed_node_ids = [item[0] for item in db.session.query(Node).with_entities(Node.id).filter(
            or_(Node.state == Node.REMOVED, Node.state == Node.DELETED)).all()]
        query_set = db.session.query(Rule, db.func.count(Alerts.id)).outerjoin(Alerts, and_(Alerts.rule_id == Rule.id, Alerts.node_id.notin_(removed_node_ids), or_(Alerts.status == None, Alerts.status != Alerts.RESOLVED)))
    else:
        query_set = db.session.query(Rule)
    query_set = query_set.filter(
        Rule.name.ilike('%' + searchterm + '%')
        )
    if alerts_count:
        query_set = query_set.group_by(Rule)
    return query_set.order_by(desc(db.func.count(Alerts.id)), asc(Rule.name))


def get_total_count():
    return Rule.query.count()


def get_rule_by_name(rule_name):
    return Rule.query.filter(Rule.name == rule_name).first()


def edit_rule_by_id(rule_id, name, alerters, description, conditions, status, updated_at, recon_queries, severity,
                    type_ip, tactics, technique_id, platform, alert_description):
    rule = get_rule_by_id(rule_id)
    return rule.update(
        name=name, alerters=alerters, description=description, conditions=conditions,
        status=status, updated_at=updated_at, recon_queries=recon_queries, severity=severity,
        type=type_ip, tactics=tactics, technique_id=technique_id, platform=platform, alert_description=alert_description
    )


def create_rule_object(name, alerters, description, conditions, status, type_ip, tactics,
                       technique_id, recon_queries, severity, platform, alert_description):
    return Rule(
        name=name, alerters=alerters, description=description, conditions=conditions, status=status, type=type_ip,
        tactics=tactics, technique_id=technique_id, recon_queries=recon_queries,
        severity=severity, platform=platform, alert_description=alert_description
    )
