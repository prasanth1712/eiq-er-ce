from polylogyx.models import Rule, Alerts, db, Node
from polylogyx.constants import ModelStatusFilters
from sqlalchemy import desc, or_, and_, asc


def get_rule_by_id(rule_id):
    return Rule.query.filter(Rule.id == rule_id).filter(Rule.status!=Rule.DELETED).first()


def get_rules_by_ids(ids):
    return Rule.query.filter(Rule.id.in_(ids)).all()


def get_rule_name_by_id(rule_id):
    rule = Rule.query.filter(Rule.id == rule_id).first()
    return rule


def get_rule_alerts_count():
    return db.session.query(Alerts).filter(Alerts.source == Alerts.RULE)\
        .filter(ModelStatusFilters.ALERTS_NON_RESOLVED)\
        .filter(ModelStatusFilters.HOSTS_NON_DELETED).filter(Rule.status!=Rule.DELETED)\
            .join(Rule, Alerts.rule_id == Rule.id).join(Node, Alerts.node_id == Node.id).count()


def get_all_rules(searchterm='', alerts_count=False, status=True, column=None, order_by=None):
    if column:
        if column == 'name':
            order_object=Rule.name
        elif column == 'created_at':
            order_object=Rule.created_at
        elif column == 'alert_count':
            order_object = db.func.count(Alerts.id)

    if alerts_count:
        removed_node_ids = [item[0] for item in db.session.query(Node).with_entities(Node.id).filter(
            ModelStatusFilters.HOSTS_DELETED).all()]
        query_set = db.session.query(Rule, db.func.count(Alerts.id)).outerjoin(Alerts, and_(Alerts.rule_id == Rule.id, Alerts.node_id.notin_(removed_node_ids), ModelStatusFilters.ALERTS_NON_RESOLVED)).filter(Rule.status!=Rule.DELETED)
    else:
        query_set = db.session.query(Rule).filter(Rule.status!=Rule.DELETED)
    if status is not None:
        if status:
            query_set = query_set.filter(Rule.status == Rule.ACTIVE)
        else:
            query_set = query_set.filter(Rule.status == Rule.INACTIVE)
    if searchterm:
        query_set = query_set.filter(
            Rule.name.ilike('%' + searchterm + '%')
            )
    if alerts_count:
        query_set = query_set.group_by(Rule)
    if order_by and order_by in ['asc','Asc','ASC']:
        return query_set.order_by(asc(order_object))
    elif order_by and order_by in ['desc','DESC','Desc']:
        return query_set.order_by(desc(order_object))
    return query_set.order_by(desc(db.func.count(Alerts.id)), asc(Rule.name))


def get_total_count(status):
    if status is not None:
        if status:
            return Rule.query.filter(Rule.status == Rule.ACTIVE).count()
        else:
            return Rule.query.filter(Rule.status == Rule.INACTIVE).count()
    else:
        return Rule.query.count()


def get_rule_by_name(rule_name):
    return Rule.query.filter(Rule.name == rule_name).filter(Rule.status!=Rule.DELETED).first()


def edit_rule_by_id(rule_id, name, alerters, description, conditions, status, updated_at, severity,
                    type_ip, tactics, technique_id, platform, alert_description):
    rule = get_rule_by_id(rule_id)
    return rule.update(
        name=name, alerters=alerters, description=description, conditions=conditions,
        status=status, updated_at=updated_at, severity=severity,
        type=type_ip, tactics=tactics, technique_id=technique_id, platform=platform, alert_description=alert_description
    )


def create_rule_object(name, alerters, description, conditions, status, type_ip, tactics,
                       technique_id, severity, platform, alert_description):
    return Rule(
        name=name, alerters=alerters, description=description, conditions=conditions, status=status, type=type_ip,
        tactics=tactics, technique_id=technique_id,
        severity=severity, platform=platform, alert_description=alert_description
    )

def disable_rule_by_ids(ids):
    db.session.query(Rule).filter(Rule.id.in_(ids)).update({Rule.status:Rule.INACTIVE}, synchronize_session=False)


def enable_rule_by_ids(ids):
    db.session.query(Rule).filter(Rule.id.in_(ids)).update({Rule.status:Rule.ACTIVE}, synchronize_session=False)


def delete_rule_by_ids(ids):
    db.session.query(Rule).filter(Rule.id.in_(ids)).update({Rule.status:Rule.DELETED}, synchronize_session=False)


def get_rule_name_rule_ids():
    query_set = db.session.query(Rule).filter(Rule.status != Rule.DELETED).order_by(Rule.name).all()
    return query_set