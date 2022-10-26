from flask import current_app
from polylogyx.models import ResultLog, db, Node, OsquerySchema,VirusTotalAvEngines,DownloadCsvExport,DefaultFilters,NodeConfig
from polylogyx.constants import PolyLogyxServerDefaults, ModelStatusFilters
from polylogyx.cache import get_a_host

from operator import and_
from sqlalchemy import desc
import datetime as dt


def del_result_log_obj(since):
    return ResultLog.query.filter(ResultLog.timestamp < since).delete()


def getResponseEnabledStatus(node):
    from polylogyx.dao.v1 import configs_dao
    config = configs_dao.get_config_of_node(node)
    default_filters_obj = DefaultFilters.query.filter(DefaultFilters.config == config).first()
    if default_filters_obj:
        if 'options' in default_filters_obj.filters.keys() :
            if 'custom_plgx_EnableRespServer' in default_filters_obj.filters['options'].keys():
                return default_filters_obj.filters['options']['custom_plgx_EnableRespServer']
            else:
                return 'true'
        else:
            return 'true'
    else:
        return 'true'


def is_last_checkin_under_checkin_time(last_checkin, host_identifier, node_key):
    host = get_a_host(node_key=node_key)
    if host and host.get('last_checkin'):
        last_checkin = dt.datetime.strptime(host.get('last_checkin'), "%Y-%m-%d %H:%M:%S.%f")
    checkin_interval = current_app.config['POLYLOGYX_CHECKIN_INTERVAL']
    if isinstance(checkin_interval, (int, float)):
        checkin_interval = dt.timedelta(seconds=checkin_interval)
    if last_checkin and dt.datetime.utcnow() - last_checkin < checkin_interval:
        return True
    return False


def get_degrade_status_of_all_hosts():
    configs = db.session.execute('''select case when (default_filters.filters->'options' ) IS NULL then '{"schedule_splay_percent": 10}' 
                else default_filters.filters->'options' end, node.host_identifier, node.last_checkin, node.node_key 
                from default_filters INNER JOIN node_config on node_config.config_id=default_filters.config_id INNER JOIN node 
                on node.id=node_config.node_id and node.state!= 1 and node.state!=2; ''')
    host_options = {}
    for config in configs:
        if not config[0]:
            host_options[config[1]] = False
        elif config[1] not in host_options:
            host_options[config[1]] = {}
            if 'custom_plgx_EnableRespServer' in config[0].keys():
                host_options[config[1]] = config[0]['custom_plgx_EnableRespServer']
            else:
                host_options[config[1]] = 'true'
            if is_last_checkin_under_checkin_time(config[2], config[1], config[3]) and host_options[config[1]] in ['true', 'True', 'TRUE']:
                host_options[config[1]] = True
            else:
                host_options[config[1]] = False
    db.session.commit()
    return host_options


def result_log_query(lines, type, node_id, query_name, start, limit):
    base_qs = db.session.query(ResultLog.node_id, ResultLog.name, ResultLog.columns).filter(ResultLog.action != "removed").filter(ResultLog.node_id.in_(node_id)).filter(ResultLog.name == query_name).filter(
      ResultLog.columns[type].astext.in_(lines)).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, ResultLog.node_id == Node.id)
    results = base_qs.offset(start).limit(limit).all()
    count = base_qs.count()
    return {'count':count, 'results':results}


def result_log_query_for_export(lines, type, node_id, query_name):
    return db.session.query(ResultLog.columns).filter(ResultLog.name == query_name).filter(ResultLog.node_id.in_(node_id)).filter(
        ResultLog.columns[type].astext.in_(lines)).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, ResultLog.node_id == Node.id).all()


def result_log_search_results(filter,node_ids,query_name,offset,limit):
    base_qs = db.session.query(ResultLog.columns).filter(*filter).filter(ResultLog.node_id.in_(node_ids)).filter(
    ResultLog.name == query_name).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, ResultLog.node_id == Node.id)
    count = base_qs.count()
    results = base_qs.offset(offset).limit(limit).all()
    return {'count':count, 'results':results}


def result_log_query_count(lines,type):
    return db.session.query(ResultLog.node_id, ResultLog.name, db.func.count(ResultLog.columns)).filter(
        ResultLog.columns[type].astext.in_(lines)).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, ResultLog.node_id == Node.id).group_by(ResultLog.node_id,ResultLog.name).all()


def result_log_search_results_count(filter):
    return db.session.query(ResultLog.node_id, ResultLog.name, db.func.count(ResultLog.columns)).filter(*filter).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, ResultLog.node_id == Node.id).group_by(ResultLog.node_id,
                                                                                               ResultLog.name).all()


def fetch_virus_total_av_engines():
    av_engines = db.session.query(VirusTotalAvEngines.name,VirusTotalAvEngines.status).all()
    data = {}
    for av_engine in av_engines:
        data[av_engine.name]={}
        data[av_engine.name]['status']=av_engine.status
    return data


def update_av_engine_status(av_engines):
    for key in list(av_engines.keys()):
        av_engine = db.session.query(VirusTotalAvEngines).filter(VirusTotalAvEngines.name == key).first()
        if av_engine:
            av_engine.update(status=av_engines[key]['status'])
    av_engine_data = {"av_engines": av_engines}
    return av_engine_data


def results_with_indicators_filtered(lines, type, node_ids, query_name, start, limit, start_date, end_date):
    base_qs = db.session.query(ResultLog).filter(ResultLog.action != "removed").filter(
      ResultLog.columns[type].astext.in_(lines)).filter(ModelStatusFilters.HOSTS_NON_DELETED)\
        .join(Node, ResultLog.node_id == Node.id)
    if node_ids:
        base_qs = base_qs.filter(ResultLog.node_id.in_(node_ids))
    if query_name:
        base_qs = base_qs.filter(ResultLog.name == query_name)
    base_qs = base_qs.filter(ResultLog.timestamp >= start_date).filter(ResultLog.timestamp <= end_date)\
        .order_by(desc(ResultLog.id))
    count = base_qs.count()
    if start:
        base_qs = base_qs.filter(ResultLog.id < start)
    results = base_qs.limit(limit).all()
    return {'count': count, 'results': [result.as_dict() for result in results]}


def results_with_indicators_filtered_to_export(lines, type, node_ids, query_name, start_date, end_date):
    query_set = db.session.query(ResultLog.columns).filter(ResultLog.columns[type].astext.in_(lines)).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, ResultLog.node_id == Node.id)
    if node_ids:
        query_set = query_set.filter(ResultLog.node_id.in_(node_ids))
    if query_name:
        query_set = query_set.filter(ResultLog.name == query_name)
    query_set = query_set.filter(ResultLog.timestamp >= start_date).filter(ResultLog.timestamp <= end_date)
    return query_set.all()


def record_query(node_id, query_name):
    return db.session.query(ResultLog.columns).filter(
            and_(ResultLog.node_id == (node_id), and_(ResultLog.name == query_name, ResultLog.action != 'removed'))).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, ResultLog.node_id == Node.id).all()


def result_log_search_query(filter, node_ids, query_name, start, limit, start_date, end_date):
    base_qs = db.session.query(ResultLog).filter(*filter)\
        .filter(ModelStatusFilters.HOSTS_NON_DELETED)\
        .join(Node, ResultLog.node_id == Node.id)
    if node_ids:
        base_qs = base_qs.filter(ResultLog.node_id.in_(node_ids))
    if query_name:
        base_qs = base_qs.filter(ResultLog.name == query_name)
    base_qs = base_qs.filter(ResultLog.timestamp >= start_date).filter(ResultLog.timestamp <= end_date)\
        .filter(ResultLog.created_at >= start_date)\
        .order_by(desc(ResultLog.id))
    count = base_qs.count()
    if start:
        base_qs = base_qs.filter(ResultLog.id < start)
    results = base_qs.limit(limit).all()
    return {'count': count, 'results': [result.as_dict() for result in results]}


def get_osquery_agent_schema():
    return OsquerySchema.query.order_by(OsquerySchema.name.asc()).all()


def create_csv_export_object(name, task_id, status):
    return DownloadCsvExport(name=name, task_id=task_id, status=status)


def update_csv_export_status(task_id, status):
    db.session.query(DownloadCsvExport).filter(DownloadCsvExport.task_id == task_id).update({'status': status})
