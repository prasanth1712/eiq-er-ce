import datetime as dt

from flask import current_app

from sqlalchemy import or_,desc, and_, cast, not_
import sqlalchemy
from sqlalchemy.sql import functions

from polylogyx.models import db, Node, ResultLog, Tag, StatusLog, NodeQueryCount, Alerts, Rule
from polylogyx.constants import ModelStatusFilters


def get_all_nodes():
    return Node.query.filter(and_(Node.state != Node.REMOVED, Node.state != Node.DELETED)).order_by(desc(Node.id)).all()


def get_node_by_host_identifier(host_identifier):
    return db.session.query(Node).filter(
            or_(Node.host_identifier == host_identifier, Node.node_key == host_identifier)).filter(Node.state != Node.DELETED).first()


def get_disable_node_by_host_identifier(host_identifier):
    return db.session.query(Node).filter(Node.state == Node.REMOVED).filter(
        or_(Node.host_identifier == host_identifier, Node.node_key == host_identifier)).first()


def get_disable_node_by_id(node_id):
    return db.session.query(Node).filter(and_(Node.id == node_id, Node.state == Node.REMOVED)).first()


def get_all_node_by_host_identifier(host_identifier):
    return db.session.query(Node).filter(or_(
        Node.host_identifier == host_identifier, Node.node_key == host_identifier, Node.state != Node.DELETED, Node.state != Node.REMOVED)).first()


def get_nodes_list_by_host_ids(host_identifiers, tags=[], platform=None):
    if platform == 'linux':
        platform_filter = [~Node.platform.in_(('windows', 'darwin', 'freebsd'))]
    else:
        platform_filter = [Node.platform == platform]
    query_set = db.session.query(Node).filter(or_(Node.host_identifier.in_(host_identifiers), Node.tags.any(Tag.value.in_(tags))))
    if platform:
        query_set = query_set.filter(and_(*platform_filter))
    return query_set.all()


def get_nodes_by_host_ids(host_identifiers):
    return db.session.query(Node).filter(Node.host_identifier.in_(host_identifiers))\
        .filter(ModelStatusFilters.HOSTS_ENABLED).all()


def get_host_id_and_name_by_node_id(node_id):
    node = get_node_by_id(node_id)
    if node:
        return {'hostname': node.display_name, 'host_identifier': node.host_identifier}


def get_node_by_id(node_id):
    return db.session.query(Node).filter(and_(Node.id == node_id)).filter(Node.state != Node.DELETED).first()


def get_all_nodes_by_id(node_id):
    return db.session.query(Node).filter(Node.id == node_id).filter(Node.state != Node.DELETED).first()


def get_host_name_by_node_id(node_id):
    query = db.session.query(Node).filter(Node.id == node_id).filter(Node.state != Node.DELETED).first()
    if query:
        return query.display_name


def get_result_log_count(node_id):
    return db.session.query(NodeQueryCount.query_name, functions.sum(cast(NodeQueryCount.total_results,
                                                                          sqlalchemy.INTEGER))) \
            .filter(NodeQueryCount.node_id == node_id).group_by(NodeQueryCount.query_name).all()


def get_result_log_of_a_query(node_id, query_name, start, limit, searchterm, column_name, column_value):
    count_categorized_results = False
    categorized_count = 0
    total_count = 0
    if (column_name == 'eventid' and len(column_value) == 1 and column_value[0] == '18') or column_name == 'defender_event_id':
        count_qs_total = db.session.query(functions.sum(cast(NodeQueryCount.total_results, sqlalchemy.INTEGER)))\
            .filter(NodeQueryCount.node_id == node_id).filter(NodeQueryCount.query_name == query_name)\
            .filter(NodeQueryCount.event_id == column_value[0]).first()
    else:
        count_qs_total = db.session.query(functions.sum(cast(NodeQueryCount.total_results, sqlalchemy.INTEGER)))\
            .filter(NodeQueryCount.node_id == node_id).filter(NodeQueryCount.query_name == query_name).first()
    if count_qs_total and count_qs_total[0]:
        total_count = count_qs_total[0]
    if column_name and column_name == 'eventid':
        categorized_count_qs = db.session.query(functions.sum(cast(NodeQueryCount.total_results, sqlalchemy.INTEGER)))\
            .filter(NodeQueryCount.node_id == node_id).filter(NodeQueryCount.query_name == query_name)\
            .filter(NodeQueryCount.event_id.in_(column_value)).first()
        if categorized_count_qs and categorized_count_qs[0]:
            categorized_count = categorized_count_qs[0]
        count_categorized_results = False
    query_string = """select id,timestamp,action ,columns::jsonb from result_log
                where node_id={0} and name='{1}' and action!='removed'""".format(str(node_id), query_name)
    if column_name and column_value:
        if count_categorized_results:
            count_query = """select count(id) from result_log where node_id='{0}' 
                and name='{1}' and action!='removed'""".format(str(node_id), query_name)
            if column_name == 'defender_event_id':
                count_query = "{0} and columns::jsonb ->> 'eventid'='18'".format(count_query)
            if len(column_value) == 1:
                count_query = "{0} and columns::jsonb ->> '{1}'='{2}'".format(count_query, column_name, column_value[0])
            else:
                count_query = "{0} and columns::jsonb ->> '{1}' in {2}".format(count_query, column_name, column_value)
            count_query = "{0} group by id order by id desc;".format(count_query)
            categorized_count = db.session.execute(sqlalchemy.text(count_query))
            categorized_count = categorized_count.rowcount
        if column_name == 'defender_event_id':
            query_string = "{0} and columns::jsonb ->> 'eventid'='18'".format(query_string)
        if len(column_value) == 1:
            query_string = "{0} and columns::jsonb ->> '{1}'='{2}'".format(query_string, column_name, column_value[0])
        else:
            query_string = "{0} and columns::jsonb ->> '{1}' in {2}".format(query_string, column_name, column_value)
    else:
        categorized_count = total_count

    if searchterm:
        query_string = "select id,timestamp,action,columns from result_log, jsonb_each(columns) objects  where  " \
                    "node_id='{0}' and name='{1}' and action!='removed' and objects.value::text ilike '%{2}%'".format(str(node_id), query_name,searchterm)
        count_query_string = "select count(id) from result_log, jsonb_each(columns) objects  where  " \
                             "node_id='{0}' and name='{1}' and action!='removed' and objects.value::text ilike '%{2}%' ".format(str(node_id), query_name,searchterm)
        if column_name and column_value:
            if column_name == 'defender_event_id':
                count_query_string = "{0} and columns::jsonb->> 'eventid'='18'".format(count_query_string)
                query_string = "{0} and columns::jsonb->> 'eventid'='18'".format(query_string)
            if len(column_value) == 1:
                count_query_string = "{0} and columns::jsonb ->> '{1}'='{2}'".format(count_query_string, column_name,
                                                                              column_value[0])
                query_string = "{0} and columns::jsonb ->> '{1}'='{2}'".format(query_string, column_name,
                                                                              column_value[0])
            else:
                count_query_string = "{0} and columns::jsonb ->> '{1}' in {2}".format(count_query_string, column_name,
                                                                               column_value)
                query_string = "{0} and columns::jsonb ->> '{1}' in {2}".format(query_string, column_name,
                                                                                      column_value)
        count_query_string = "{0} group by id,timestamp,action,columns order by timestamp desc;".format(count_query_string)

        query_count = db.session.execute(sqlalchemy.text(count_query_string))
        query_count = query_count.rowcount
    else:
        query_count = categorized_count
    if start:
        if searchterm:
            query_string = "{0} and id<{1} group by id,timestamp,action,columns order by id desc LIMIT {2}".format(query_string, start, limit)
        else:
            query_string = "{0} and id<{1} order by id desc LIMIT {2}".format(query_string, start, limit)
    else:
        query_string = "{0}  order by id desc LIMIT {2}".format(
            query_string, start, limit)
    query_results = db.session.execute(sqlalchemy.text(query_string))
    db.session.commit()
    return query_count, query_results, total_count, categorized_count


def extend_nodes_by_node_key_list(node_key_list):
    return Node.query.filter(or_(
                        Node.node_key.in_(node_key_list), Node.host_identifier.in_(node_key_list)))\
        .filter(ModelStatusFilters.HOSTS_ENABLED).all()


def extend_nodes_by_tag(tags):
    return Node.query.filter(Node.tags.any(Tag.value.in_(tags))).filter(ModelStatusFilters.HOSTS_ENABLED).all()


def node_result_log_search_results(filter, node_id, query_name, column_name=None, column_value=None):
    qs = db.session.query(ResultLog.columns).filter(ResultLog.name == query_name)
    if column_name and column_value:
        qs = qs.filter(ResultLog.columns[column_name].astext.in_(column_value))
    if filter:
        qs = qs.filter(*filter)
    if node_id:
        qs = qs.filter(ResultLog.node_id == node_id)
    return qs.all()


def get_hosts_filtered_status_platform_count():
    from sqlalchemy import and_
    linux_filter = [~Node.platform.in_(('windows', 'darwin'))]

    checkin_interval = current_app.config['POLYLOGYX_CHECKIN_INTERVAL']
    current_time = dt.datetime.utcnow() - checkin_interval
    linux_online = db.session.query(db.func.count(Node.id)).filter(or_(Node.is_active,
            Node.last_checkin > current_time)).filter(and_(*linux_filter)).filter(and_(Node.state != Node.REMOVED, Node.state != Node.DELETED)).scalar()
    linux_offline = db.session.query(db.func.count(Node.id)).filter(and_(not_(Node.is_active),
            Node.last_checkin < current_time)).filter(and_(*linux_filter)).filter(and_(Node.state != Node.REMOVED, Node.state != Node.DELETED)).scalar()

    windows_online = db.session.query(db.func.count(Node.id)).filter(or_(Node.is_active,
            Node.last_checkin > current_time)).filter(and_(Node.platform == "windows", Node.state != Node.REMOVED, Node.state != Node.DELETED)).scalar()
    windows_offline = db.session.query(db.func.count(Node.id)).filter(and_(not_(Node.is_active),
            Node.last_checkin < current_time)).filter(and_(Node.platform == "windows", Node.state != Node.REMOVED, Node.state != Node.DELETED)).scalar()

    darwin_online = db.session.query(db.func.count(Node.id)).filter(or_(Node.is_active,
            Node.last_checkin > current_time)).filter(and_(Node.platform == "darwin", Node.state != Node.REMOVED, Node.state != Node.DELETED)).scalar()
    darwin_offline = db.session.query(db.func.count(Node.id)).filter(and_(not_(Node.is_active),
            Node.last_checkin < current_time)).filter(and_(Node.platform == "darwin", Node.state != Node.REMOVED, Node.state != Node.DELETED)).scalar()
    return {'windows': {'online': windows_online, 'offline': windows_offline}, 'linux': {'online': linux_online, 'offline': linux_offline}, 'darwin':{'online': darwin_online, 'offline': darwin_offline}}


def get_hosts_paginated(status, platform, searchterm="", enabled=True, alerts_count=False):
    checkin_interval = current_app.config['POLYLOGYX_CHECKIN_INTERVAL']
    online_filter = or_(Node.is_active, dt.datetime.utcnow() - Node.last_checkin < checkin_interval)
    offline_filter = and_(not_(Node.is_active), dt.datetime.utcnow() - Node.last_checkin > checkin_interval)

    filter = []
    if platform == 'linux':
        filter.append(~Node.platform.in_(('windows', 'darwin')))
    else:
        filter.append(Node.platform == platform)

    if alerts_count:
        query_set = db.session.query(Node, db.func.count(Alerts.id)).outerjoin(Alerts, and_(Alerts.node_id == Node.id, or_(Alerts.status == None, Alerts.status != Alerts.RESOLVED)))
    else:
        query_set = db.session.query(Node)
    if platform:
        query_set = query_set.filter(*filter)
    if enabled:
        query_set = query_set.filter(and_(Node.state != Node.REMOVED, Node.state != Node.DELETED))
    else:
        query_set = query_set.filter(Node.state == Node.REMOVED)
    if searchterm:
        query_set = query_set.filter(or_(
            Node.node_info['display_name'].astext.ilike('%' + searchterm + '%'),
            Node.node_info['computer_name'].astext.ilike('%' + searchterm + '%'),
            Node.node_info['hostname'].astext.ilike('%' + searchterm + '%'),
            Node.os_info['name'].astext.ilike('%' + searchterm + '%'),
            cast(Node.last_ip, sqlalchemy.String).ilike('%' + searchterm + '%'),
            Node.tags.any(Tag.value.in_([searchterm]))
        ))
    if status is not None:
        if status:
            query_set = query_set.filter(online_filter)
        else:
            query_set = query_set.filter(offline_filter)
    if alerts_count:
        return query_set.group_by(Node).order_by(desc(online_filter), desc(db.func.count(Alerts.id)), desc(Node.id))
    return query_set.order_by(desc(online_filter), desc(Node.id))


def get_hosts_total_count(status, platform, enabled=True):
    filter = []
    if platform == 'linux':
        filter.append(~Node.platform.in_(('windows', 'darwin')))
    else:
        filter.append(Node.platform == platform)

    checkin_interval = current_app.config['POLYLOGYX_CHECKIN_INTERVAL']
    if platform:
        qs = Node.query.filter(*filter)
    else:
        qs = Node.query
    if enabled:
        qs = qs.filter(and_(Node.state != Node.REMOVED, Node.state != Node.DELETED))
    else:
        qs = qs.filter(Node.state == Node.REMOVED)
    if status is not None:
        if status:
            qs = qs.filter(or_(Node.is_active,dt.datetime.utcnow() - Node.last_checkin < checkin_interval))
        else:
            qs = qs.filter(and_(not_(Node.is_active),dt.datetime.utcnow() - Node.last_checkin > checkin_interval))
    return qs.count()


def get_status_logs_of_a_node(node, searchterm=''):
    return StatusLog.query.filter_by(node=node).filter(or_(
        StatusLog.message.ilike('%' + searchterm + '%'),
        StatusLog.filename.ilike('%' + searchterm + '%'),
        StatusLog.version.ilike('%' + searchterm + '%'),
        cast(StatusLog.created, sqlalchemy.String).ilike('%' + searchterm + '%'),
        cast(StatusLog.line, sqlalchemy.String).ilike('%' + searchterm + '%'),
        cast(StatusLog.severity, sqlalchemy.String).ilike('%' + searchterm + '%')
        )).order_by(desc(StatusLog.id))


def get_status_logs_total_count(node):
    return StatusLog.query.filter_by(node=node).count()


def get_tagged_nodes(tag_names):
    if tag_names is None:
        nodes = Node.query.filter(Node.tags == None).all()
    else:
        nodes = Node.query.filter(and_(Node.tags.any(Tag.value.in_(tag_names))), Node.state != Node.DELETED, Node.state != Node.REMOVED).all()
    print(nodes)
    return nodes


def is_tag_of_node(node, tag):
    if tag in node.tags:
        return True
    else:
        return False


def soft_remove_host(node):
    return node.update(state=Node.REMOVED, updated_at=dt.datetime.now())


def delete_host(node):
    return node.update(state=Node.DELETED, updated_at=dt.datetime.now())


def enable_host(node):
    return node.update(state=Node.ACTIVE, updated_at=dt.datetime.now())


def host_alerts_distribution_by_source(node):
    alert_count = db.session.query(Alerts.source, Alerts.severity, db.func.count(
        Alerts.id)).filter(or_(Alerts.status == None, Alerts.status != Alerts.RESOLVED))\
        .filter(Alerts.node_id == node.id).group_by(Alerts.source, Alerts.severity).all()

    alert_distro = {'ioc': {'INFO': 0, 'LOW': 0, 'WARNING': 0, 'CRITICAL': 0},
                  'rule': {'INFO': 0, 'LOW': 0, 'WARNING': 0, 'CRITICAL': 0},
                  'virustotal': {'INFO': 0, 'LOW': 0, 'WARNING': 0, 'CRITICAL': 0},
                  'ibmxforce': {'INFO': 0, 'LOW': 0, 'WARNING': 0, 'CRITICAL': 0},
                  'alienvault': {'INFO': 0, 'LOW': 0, 'WARNING': 0, 'CRITICAL': 0}}

    for alert in alert_count:
        alert_distro[alert[0]][alert[1]] = alert[2]

    for key in alert_distro.keys():
        alert_distro[key]['TOTAL'] = alert_distro[key]['INFO'] + alert_distro[key]['LOW'] + alert_distro[key]['WARNING'] + \
                                   alert_distro[key]['CRITICAL']
    return alert_distro


def host_alerts_distribution_by_rule(node):
    return db.session.query(Rule.name, db.func.count(Alerts.id)).filter(Alerts.source == Alerts.RULE)\
        .join(Alerts.rule).filter(or_(Alerts.status == None, Alerts.status != Alerts.RESOLVED))\
        .filter(Alerts.node_id == node.id).group_by(Rule.name).order_by(db.func.count(Alerts.rule_id).desc()).limit(5).all()


def get_hosts_from_os_names(os_names):
    return db.session.query(Node).filter(Node.os_info['name'].astext.in_(os_names))\
        .filter(ModelStatusFilters.HOSTS_ENABLED).all()


def get_host_by_host_identifiers(host_ids):
    return Node.query.filter(Node.host_identifier.in_(host_ids)).filter(and_(Node.state != Node.DELETED, Node.state != Node.REMOVED)).all()


def get_result_log_of_a_query_opt(node_id, query_name, start=None, limit=None, searchterm=None , column_name=None, column_value=None):

    categorized_count = 0
    total_count = 0

    # Node query count - nqq - Start
    if column_name not in ['defender_event_id']:
        nqq_basequery = NodeQueryCount.query\
                        .with_entities(functions.sum(NodeQueryCount.total_results))\
                        .filter(NodeQueryCount.node_id == node_id) \
                        .filter(NodeQueryCount.query_name == query_name)
        nqq_query=nqq_basequery
        
        nqq_query_count = nqq_query.first()

        total_count = nqq_query_count[0] or 0
        categorized_count=total_count

        if column_name == 'eventid':
            nqq_query = nqq_query.filter(NodeQueryCount.event_id.in_(column_value))
            nqq_query_cat_count = nqq_query.first()
            categorized_count = nqq_query_cat_count[0] or 0

    # Node query count - End
    
    # Result Log Fetch - Start 
    rl_basequery = ResultLog.query.with_entities(ResultLog.id,ResultLog.timestamp,ResultLog.action,ResultLog.columns)\
                   .filter(ResultLog.node_id==str(node_id),ResultLog.name==query_name,ResultLog.action!="removed")

    rl_query = rl_basequery

    if column_name and column_value:
        if column_name=="defender_event_id":
            rl_query=rl_query.filter(ResultLog.columns.has_key(column_name))
            total_count = rl_query.count()
            categorized_count=total_count
        rl_query=rl_query.filter(ResultLog.columns[column_name].astext.in_(column_value))
    
    if searchterm:
        rl_query = rl_query.filter(ResultLog.columns.cast(sqlalchemy.Text).contains(searchterm))
        

    rl_query = rl_query.order_by(ResultLog.id.desc())
    search_count =  rl_query.count()

    if start:
        rl_query = rl_query.filter(ResultLog.id<start)
    
    if limit:
        rl_query=rl_query.limit(limit)

    query_results=rl_query.all()

    db.session.rollback()
    return search_count, query_results, total_count, categorized_count


def topFiveNodes(date):
    return  db.session.query(
            sqlalchemy.func.sum(NodeQueryCount.total_results),Node).join(Node,and_(NodeQueryCount.node_id == Node.id, Node.state == Node.ACTIVE)) \
         .filter(NodeQueryCount.date==date).group_by(Node.id).order_by(desc(sqlalchemy.func.sum(NodeQueryCount.total_results))).limit(5). \
            all()