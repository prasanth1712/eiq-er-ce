from polylogyx.models import ResultLog, Options, db, Node, NodeReconData, NodeData
from polylogyx.constants import PolyLogyxServerDefaults

from sqlalchemy import text
from operator import and_


def del_result_log_obj(since):
    return ResultLog.query.filter(ResultLog.timestamp < since).delete()


def get_result_log_since(since):
    return ResultLog.query.filter(ResultLog.timestamp < since).all()


def options_query():
    return Options.query.filter(Options.name == PolyLogyxServerDefaults.plgx_config_all_options).first()


def options_filter_by_key(k):
    return Options.query.filter(Options.name == k).first()


def create_option(k,v):
    return Options.create(name=k, option=v)


def create_option_by_option(option):
    return Options.create(name=PolyLogyxServerDefaults.plgx_config_all_options, option=option)


def result_log_query(lines,type,offset,limit):
    return db.session.query(ResultLog.node_id, ResultLog.name, ResultLog.columns).filter(
        ResultLog.columns[type].astext.in_(lines)).offset(offset).limit(limit).all()


def record_query(node_id, query_name):
    return db.session.query(ResultLog.columns).filter(
            and_(ResultLog.node_id == (node_id), and_(ResultLog.name == query_name, ResultLog.action != 'removed'))).all()


def search_query(filter_node_recon):
    return db.session.query(NodeReconData).join(
            NodeData, NodeReconData.node_data).options(
            db.lazyload('*'),
            db.contains_eager(NodeReconData.node_data),
        ).with_entities(NodeData.node_id, NodeData.name, NodeData.data).filter(
            *filter_node_recon).group_by(NodeData.node_id, NodeData.name, NodeData.data).all()


def result_log_search_results(filter,node_id,query_name,offset,limit):
    return db.session.query(ResultLog.columns).filter(*filter).filter(ResultLog.node_id == node_id).filter(
        ResultLog.name == query_name).offset(offset).limit(limit).all()


def result_log_query_count(lines,type):
    return db.session.query(ResultLog.node_id, ResultLog.name, db.func.count(ResultLog.columns)).filter(
        ResultLog.columns[type].astext.in_(lines)).group_by(ResultLog.node_id,ResultLog.name).all()


def result_log_search_results_count(filter):
    return db.session.query(ResultLog.node_id, ResultLog.name, db.func.count(ResultLog.columns)).filter(*filter).group_by(ResultLog.node_id,
                                                                                               ResultLog.name).all()