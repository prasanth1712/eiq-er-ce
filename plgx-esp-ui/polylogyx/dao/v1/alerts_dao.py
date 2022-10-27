import datetime

from polylogyx.models import db, Alerts, ResultLog, Rule, Node, NodeQueryCount, AlertLog,AnalystNotes ,PlatformActivity ,User

from sqlalchemy import func, cast, INTEGER, desc, or_, and_, asc ,case
import sqlalchemy
import datetime as dt
from sqlalchemy.sql import functions

from polylogyx.util.constants import DEFAULT_PROCESS_GRAPH_QUERIES
from polylogyx.constants import ModelStatusFilters
from polylogyx.db.signals import bulk_insert_to_pa

process_guid_column = 'process_guid'
parent_process_guid_column = 'parent_process_guid'


def get_alert_by_id(alert_id):
    return Alerts.query.filter_by(id=alert_id).first()


def get_alert_source(source, start_date, end_date, node, rule_id, event_ids, severity, verdict, search):
    severity_dict = {
        'critical': Alerts.CRITICAL,
        'medium': Alerts.MEDIUM,
        'info': Alerts.INFO,
        'high': Alerts.HIGH,
        'low': Alerts.LOW
    }
    verdict_dict = {
        'true_positive': Alerts.TRUE_POSITIVE,
        'false_positive': Alerts.FALSE_POSITIVE,
        'open': Alerts.NA
    }
    qs = db.session.query(Alerts).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, Alerts.node_id == Node.id)
    if source:
        qs=qs.filter(Alerts.source.in_(source))
    if node:
        qs = qs.filter(Alerts.node_id.in_( node))
    if rule_id:
        qs = qs.filter(Alerts.rule_id.in_(rule_id))
    if start_date and end_date:
        qs = qs.filter(Alerts.created_at >= start_date).filter(Alerts.created_at <= end_date)
    if event_ids:
        qs = qs.filter(Alerts.id.in_(event_ids))
    if severity:
        qs = qs.filter(Alerts.severity.in_([severity_dict[st] for st in severity]))
    if verdict:
        qs = qs.filter(Alerts.verdict.in_([verdict_dict[vd] for vd in verdict]))
    if start_date and end_date:
        qs = qs.filter(Alerts.created_at >= start_date).filter(Alerts.created_at <= end_date)
    if search :
        qs = qs.outerjoin(Rule)
        qs = qs.filter(or_(
            Alerts.severity.ilike('%' + search + '%'),
            Node.node_info['computer_name'].astext.ilike('%' + search + '%'),
            Node.node_info['display_name'].astext.ilike('%' + search + '%'),
            Node.node_info['hostname'].astext.ilike('%' + search + '%'),
            Rule.name.ilike('%' + search + '%')))
    return qs.order_by(desc(Alerts.id)).all()


def get_distinct_alert_source(resolved, start_date, end_date, node, rule_id):
    if  resolved is False:
        qs = db.session.query(Alerts).with_entities(Alerts.source, db.func.count(Alerts.source)).filter(
            ModelStatusFilters.ALERTS_NON_RESOLVED).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node,
            Alerts.node_id == Node.id).order_by(Alerts.source).group_by(Alerts.source)
    elif resolved is True:
        qs = db.session.query(Alerts).with_entities(Alerts.source, db.func.count(Alerts.source)).filter(
            ModelStatusFilters.ALERTS_RESOLVED).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, 
            Alerts.node_id == Node.id).order_by(Alerts.source).group_by(Alerts.source)
    else:
        qs = db.session.query(Alerts).with_entities(Alerts.source, db.func.count(Alerts.source)).filter(
            ModelStatusFilters.HOSTS_NON_DELETED).join(Node, Alerts.node_id == Node.id).order_by(
            Alerts.source).group_by(Alerts.source)
    if node:
        qs = qs.filter(Alerts.node_id == node.id)
    if rule_id:
        qs = qs.filter(Alerts.rule_id == rule_id)
    if start_date and end_date:
        qs = qs.filter(Alerts.created_at >= start_date).filter(Alerts.created_at <= end_date)
    return qs.all()


def get_alerts_severity_with_id_timestamp(source, start_date, end_date, node, rule_id,severity=None,verdict=None,search=None):
    severity_dict = {
        'critical': Alerts.CRITICAL,
        'medium': Alerts.MEDIUM,
        'info': Alerts.INFO,
        'high': Alerts.HIGH,
        'low': Alerts.LOW
    }
    verdict_dict = {
        'true_positive': Alerts.TRUE_POSITIVE,
        'false_positive': Alerts.FALSE_POSITIVE,
        'open': Alerts.NA
    }
    qs = db.session.query(Alerts).with_entities(Alerts.id, Alerts.severity, Alerts.created_at).filter(
        ModelStatusFilters.HOSTS_NON_DELETED).join(Node, Alerts.node_id == Node.id).order_by(desc(Alerts.id))
    if source:
        qs=qs.filter(Alerts.source.in_(source))
    if node:
        qs = qs.filter(Alerts.node_id.in_(node))
    if rule_id:
        qs = qs.filter(Alerts.rule_id.in_(rule_id))
    if severity:
        qs = qs.filter(Alerts.severity.in_([severity_dict[st] for st in severity]))
    if verdict:
        qs = qs.filter(Alerts.verdict.in_([verdict_dict[vd] for vd in verdict]))
    if start_date and end_date:
        qs = qs.filter(Alerts.created_at >= start_date).filter(Alerts.created_at <= end_date)
    if search :
        qs = qs.outerjoin(Rule)
        qs = qs.filter(or_(
            Alerts.severity.ilike('%' + search + '%'),
            Node.node_info['computer_name'].astext.ilike('%' + search + '%'),
            Node.node_info['display_name'].astext.ilike('%' + search + '%'),
            Node.node_info['hostname'].astext.ilike('%' + search + '%'),
            Rule.name.ilike('%' + search + '%')))
    return qs.all()


def get_alerts_by_alert_id(alert_id):
    return Alerts.query.filter_by(id=alert_id).first()


def get_platform_activity_by_alert_id(alert_id):
    pf_qs = PlatformActivity.query.filter(and_(PlatformActivity.entity_id == alert_id,PlatformActivity.entity == 'alerts'))\
        .order_by(desc(PlatformActivity.created_at)).first()
    return pf_qs


def edit_alerts_status_by_alert(alert_ids, status=False, verdict=None, comment=None):
    alerts = Alerts.query.filter(Alerts.id.in_(alert_ids)).all()
    if status:
        status = Alerts.RESOLVED
        if verdict:
            verdict_value = Alerts.TRUE_POSITIVE
        else:
            verdict_value = Alerts.FALSE_POSITIVE
    else:
        status = Alerts.OPEN
        verdict_value = Alerts.NA
        comment = None
    alert_ids = [alert.id for alert in alerts]
    db.session.query(Alerts).filter(Alerts.id.in_(alert_ids)).update(
                                                                    {Alerts.status: status,
                                                                    Alerts.verdict: verdict_value,
                                                                    Alerts.comment: comment,
                                                                    Alerts.updated_at:datetime.datetime.utcnow()
                                                                    }, synchronize_session=False)
    bulk_insert_to_pa(db.session, 'updated', Alerts, alert_ids)
    db.session.commit()


def non_resolved_alert():
    return ModelStatusFilters.ALERTS_NON_RESOLVED


def resolved_alert():
    return ModelStatusFilters.ALERTS_RESOLVED


def get_record_query_by_dsc_order(filter, source, searchTerm='', event_ids=None, node_id=None, query_name=None, rule_id=None, events_count=None,column=None,order_by='asc',severity=None,verdict=None):
    severity_dict = {
        'critical':Alerts.CRITICAL, 
        'medium':Alerts.MEDIUM, 
        'low':Alerts.LOW, 
        'high':Alerts.HIGH, 
        'info':Alerts.INFO
    }
    verdict_dict = {
        'true_positive': Alerts.TRUE_POSITIVE, 
        'false_positive': Alerts.FALSE_POSITIVE,
        'open':Alerts.NA
    }

    if events_count:
        query_set = db.session.query(Alerts, db.func.count(AlertLog.id)).outerjoin(AlertLog)
    else:
        query_set = db.session.query(Alerts)
    if filter is not None:
        query_set = query_set.filter(filter).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, Alerts.node_id == Node.id)
    else:
        query_set = query_set.filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, Alerts.node_id == Node.id)
    if event_ids:
        query_set = query_set.filter(Alerts.id.in_(event_ids))
    if node_id:
        query_set = query_set.filter(Alerts.node_id.in_ (node_id))
    if query_name:
        query_set = query_set.filter(Alerts.query_name == query_name)
    if rule_id:
        query_set = query_set.filter(Alerts.rule_id.in_(rule_id))
    if source:
        query_set = query_set.filter(Alerts.source.in_(source))
    if severity:
        query_set = query_set.filter(Alerts.severity.in_([severity_dict[st] for st in severity]))
    if verdict:
        query_set = query_set.filter(Alerts.verdict.in_([verdict_dict[vd] for vd in verdict]))
    if searchTerm:
        query_set=query_set.outerjoin(Rule)
        query_set  =query_set.filter(or_(
                Alerts.severity.ilike('%' + searchTerm + '%'),
                Node.node_info['computer_name'].astext.ilike('%' + searchTerm + '%'),
                Node.node_info['display_name'].astext.ilike('%' + searchTerm + '%'),
                Node.node_info['hostname'].astext.ilike('%' + searchTerm + '%'),
                Rule.name.ilike('%' + searchTerm + '%')
            ))
    if column:
        if column == 'rule':
            query_set = query_set.join(Rule,Alerts.rule_id==Rule.id).group_by(Rule.name, Node.id, Alerts.id)
            if order_by in [None,'asc', 'ASC', 'Asc']:
                return query_set.order_by(Rule.name)
            else:
                return query_set.order_by(desc(Rule.name))
        elif column == 'hostname':
            query_set=query_set.group_by(Node.id,Alerts.id)
            if order_by in [None,'asc', 'ASC', 'Asc']:
                query_set = query_set.order_by(Node.node_info['computer_name'])
            else:
                query_set = query_set.order_by(desc(Node.node_info['computer_name']))
        elif column == 'severity':
            cs = case((Alerts.severity == Alerts.INFO, 1), (Alerts.severity == Alerts.LOW, 2),
                      (Alerts.severity == Alerts.MEDIUM, 3),
                      (Alerts.severity == Alerts.HIGH, 4), (Alerts.severity == Alerts.CRITICAL, 5))
            if order_by in [None,'asc', 'ASC', 'Asc']:
                query_set = query_set.order_by(cs)
            else:
                query_set = query_set.order_by(desc(cs))
        elif column == 'created_at':
            if order_by in [None,'asc', 'ASC', 'Asc']:
                query_set = query_set.order_by(Alerts.created_at)
            else:
                query_set = query_set.order_by(desc(Alerts.created_at))
        elif column == 'status':
            if order_by in [None,'asc', 'ASC', 'Asc']:
                query_set = query_set.order_by(Alerts.status)
            else:
                query_set = query_set.order_by(desc(Alerts.status))
    if events_count:
        query_set = query_set.group_by(Alerts.id)
    return query_set.order_by(desc(Alerts.id))


def get_record_query_total_count(filter, source, node_id=None, query_name=None, rule_id=None):
    base_query = db.session.query(Alerts)
    if source:
        base_query = base_query.filter(Alerts.source.in_(source))
    if node_id:
        base_query = base_query.filter(Alerts.node_id.in_(node_id))
    if query_name:
        base_query = base_query.filter(Alerts.query_name == query_name)
    if rule_id:
        base_query = base_query.filter(Alerts.rule_id.in_(rule_id))
    if filter is not None:
        return base_query.filter(filter).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, Alerts.node_id == Node.id).count()
    else:
        return base_query.filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, Alerts.node_id == Node.id).count()


def get_schedule_query_data(SYSTEM_EVENT_QUERIES, alert, time):
    return db.session.query(ResultLog.name, ResultLog.columns).filter(ResultLog.node_id == alert.node.id) \
        .filter(ResultLog.name.in_(SYSTEM_EVENT_QUERIES))\
        .filter(cast(ResultLog.columns["time"].astext, sqlalchemy.INTEGER) <= time + 30)\
        .filter(cast(ResultLog.columns["time"].astext, sqlalchemy.INTEGER) >= time - 30).all()


def get_child_action_node(process_guid_column_name, process_guid, action, host_id, eid, last_time):
    base_query = db.session.query(ResultLog).with_entities(ResultLog.columns).filter(ResultLog.node_id == host_id) \
        .filter(or_(ResultLog.name.in_(list(DEFAULT_PROCESS_GRAPH_QUERIES.keys())),
                and_(or_(ResultLog.name == 'windows_events', ResultLog.name == 'windows_real_time_events'),
                     ResultLog.columns['eventid'].astext.in_(list(DEFAULT_PROCESS_GRAPH_QUERIES.values()))))) \
        .filter(ResultLog.columns[process_guid_column_name].astext == process_guid)\
        .filter(ResultLog.columns['eid'].astext != eid)\
        .filter(ResultLog.columns["action"].astext == action)
    if last_time:
        base_query = base_query.filter(cast(ResultLog.columns["time"].astext, sqlalchemy.INTEGER) >= last_time)
    base_query = base_query.order_by(asc(cast(ResultLog.columns["time"].astext, sqlalchemy.INTEGER))).limit(20)
    return base_query.all()


def get_child_action_count(process_guids, host_id):
    return db.session.query(ResultLog).with_entities(ResultLog.columns[process_guid_column].astext,
                                                     db.func.count(ResultLog.columns[process_guid_column].astext)) \
        .filter(ResultLog.node_id == host_id)\
        .filter(or_(ResultLog.name.in_(list(DEFAULT_PROCESS_GRAPH_QUERIES.keys())),
                    and_(or_(ResultLog.name == 'windows_events', ResultLog.name == 'windows_real_time_events'),
                         ResultLog.columns['eventid'].astext.in_(list(DEFAULT_PROCESS_GRAPH_QUERIES.values()))))) \
        .filter(ResultLog.columns[process_guid_column].astext.in_(process_guids))\
        .filter(~ResultLog.columns["action"].astext.ilike('PROC_%'))\
        .group_by(ResultLog.columns[process_guid_column].astext).all()


def get_child_process_count(process_guids, host_id):
    return db.session.query(ResultLog).with_entities(ResultLog.columns[parent_process_guid_column].astext,
                                                     db.func.count(ResultLog.columns[parent_process_guid_column])) \
        .filter(ResultLog.node_id == host_id).filter(or_(ResultLog.name == 'win_process_events',
                                                         and_(or_(ResultLog.name == 'windows_events',
                                                                  ResultLog.name == 'windows_real_time_events'),
                                                              ResultLog.columns['eventid'] == '2'))) \
        .filter(ResultLog.columns[parent_process_guid_column].astext.in_(process_guids))\
        .filter(ResultLog.columns["action"].astext == 'PROC_CREATE')\
        .group_by(ResultLog.columns[parent_process_guid_column].astext).all()


def get_system_event_data_list(SYSTEM_STATE_QUERIES, alert):
    return db.session.query(NodeQueryCount.query_name).filter(NodeQueryCount.query_name.in_(SYSTEM_STATE_QUERIES))\
        .filter(NodeQueryCount.node_id == alert.node.id).group_by(NodeQueryCount.query_name).all()


def get_system_state_data_list(host_state_queries, alert):
    return db.session.query(NodeQueryCount.query_name, functions.sum(cast(NodeQueryCount.total_results, sqlalchemy.INTEGER)))\
        .filter(NodeQueryCount.query_name.in_(host_state_queries)).filter(NodeQueryCount.node_id == alert.node.id)\
        .group_by(NodeQueryCount.query_name).all()


def get_all_events_of_an_alert(alert, query_name, start, limit, searchterm, column_name, column_value):
    total_count_qs = "select id from alert_log where alert_id='{0}' and name='{1}' and action!='removed'".format(
        str(alert.id), query_name)
    query_string = "select id, timestamp, action, columns from alert_log join jsonb_each_text(alert_log.columns) " \
                   "e on true where alert_id='{0}' and name='{1}' and action!='removed'".format(str(alert.id), query_name)
    total_count = db.session.execute(sqlalchemy.text(total_count_qs))
    total_count = total_count.rowcount
    if searchterm or column_name and column_value:
        query_string = "{0} and e.value ilike '%{1}%'".format(query_string, searchterm)
        count_query_string = "select id from alert_log join jsonb_each_text(alert_log.columns) " \
                             "e on true where alert_id='{0}' and name='{1}' and action!='removed'".format(
            str(alert.id), query_name)
        if searchterm:
            count_query_string = "{0} and e.value ilike '%{1}%'".format(count_query_string, searchterm)
        if column_name and column_value:
            if len(column_value) == 1:
                count_query_string = "{0} and columns ->> '{1}'='{2}'".format(count_query_string, column_name,
                                                                               column_value[0])
            else:
                count_query_string = "{0} and columns ->> '{1}' in {2}".format(count_query_string, column_name,
                                                                               column_value)
        count_query_string = "{0} group by id order by id desc;".format(count_query_string)
        count_qs = db.session.execute(sqlalchemy.text(count_query_string))
        query_count = count_qs.rowcount
    else:
        query_count = total_count
    if column_name and column_value:
        if len(column_value) == 1:
            query_string = "{0} and columns ->> '{1}'='{2}'".format(query_string, column_name, column_value[0])
        else:
            query_string = "{0} and columns ->> '{1}' in {2}".format(query_string, column_name, column_value)
    query_string = "{0} group by id order by id desc OFFSET {1} LIMIT {2}".format(query_string, start, limit)
    query_results = db.session.execute(sqlalchemy.text(query_string))
    db.session.commit()
    return total_count, query_count, query_results


def get_alerted_events_to_export(alert, query_name, searchterm, column_name, column_value):
    query_string = "select columns from alert_log join jsonb_each_text(alert_log.columns) e on true " \
                   "where alert_id='{0}' and name='{1}' and action!='removed'".format(str(alert.id), query_name)
    if searchterm or column_name and column_value:
        if searchterm:
            query_string = "{0} and e.value ilike '%{1}%'".format(query_string, searchterm)
        if column_name and column_value:
            if len(column_value) == 1:
                query_string = "{0} and columns ->> '{1}'='{2}'".format(query_string, column_name, column_value[0])
            else:
                query_string = "{0} and columns ->> '{1}' in {2}".format(query_string, column_name, column_value)
    query_string = "{0} group by id;".format(query_string)
    query_results = db.session.execute(sqlalchemy.text(query_string))
    db.session.commit()
    return query_results


def get_alerted_queries(alert):
    queryset = db.session.query(AlertLog).with_entities(AlertLog.name, db.func.count(AlertLog.id)).filter(AlertLog.alert_id==alert.id).group_by(AlertLog.name).all()
    return [{"query_name": item[0], "count": item[1]} for item in queryset]


def get_child_action_node_by_process_guid(node_id, process_guid):
    return db.session.query(ResultLog).with_entities(ResultLog.columns['action'],
                                                     db.func.count(ResultLog.columns['action']))\
        .filter(ResultLog.node_id == node_id)\
        .filter(or_(ResultLog.name.in_(list(DEFAULT_PROCESS_GRAPH_QUERIES.keys())),
                    and_(or_(ResultLog.name == 'windows_events', ResultLog.name == 'windows_real_time_events'),
                         ResultLog.columns['eventid'].astext.in_(list(DEFAULT_PROCESS_GRAPH_QUERIES.values())))))\
        .filter(or_(and_(ResultLog.columns[process_guid_column].astext == process_guid, ~ResultLog.columns["action"]
                         .astext.ilike('PROC_CREATE%')),
                    and_(ResultLog.columns[parent_process_guid_column].astext == process_guid,
                         ResultLog.columns["action"].astext.ilike('PROC_CREATE%'))))\
        .group_by(ResultLog.columns['action']).all()


def get_alerted_proc_create(alert_process_guid, node_id):
    return db.session.query(ResultLog).with_entities(ResultLog.columns).filter(ResultLog.node_id == node_id)\
        .filter(or_(ResultLog.name == 'win_process_events', and_(or_(ResultLog.name == 'windows_events',
                                                                     ResultLog.name == 'windows_real_time_events'),
                                                                 ResultLog.columns['eventid'] == '2')))\
        .filter(ResultLog.columns[process_guid_column].astext == alert_process_guid)\
        .filter(ResultLog.columns['action'].astext == 'PROC_CREATE').first()


def get_analyst_notes(alert_id):
    return db.session.query(AnalystNotes).filter(AnalystNotes.alerts_id == alert_id).order_by(desc(AnalystNotes.id)).all()


def get_analyst_notes_by_id(id):
    return db.session.query(AnalystNotes).filter(AnalystNotes.id == id).first()


def add_analyst_notes_by_alert_id(alert_id,notes,user_id):
    analyst_note = AnalystNotes.create(alerts_id=alert_id, notes=notes, user_id=user_id, created_at=dt.datetime.utcnow())
    return analyst_note


def validate_user_edit_analyst_note(user_id,note_id):
    analyst_user_id = db.session.query(AnalystNotes).filter(AnalystNotes.id == note_id).first().user_id
    if user_id == analyst_user_id:
        return True
    else:
        return False


def edit_analyst_notes(user_id, note_id,notes):
    analyst_note = db.session.query(AnalystNotes).filter(AnalystNotes.id == note_id).first()
    analyst_note.update(notes=notes, updated_at=dt.datetime.utcnow(),user_id=user_id)
    db.session.commit()
    return analyst_note


def delete_analyst_notes(note_id):
    analyst_notes = db.session.query(AnalystNotes).filter(AnalystNotes.id == note_id).first()
    db.session.delete(analyst_notes)
    db.session.commit()
