import datetime as dt

from flask import current_app

from sqlalchemy import or_, text, desc
from polylogyx.models import db, Node, NodeData, ResultLog, Tag, NodeQueryCount


def get_all_nodes():
    return Node.query.all()

def get_node_by_host_identifier(host_identifier):
    return db.session.query(Node).filter(
            or_(Node.host_identifier == host_identifier, Node.node_key == host_identifier)).first()

def get_node_by_id(node_id):
    return db.session.query(Node).filter(Node.id == node_id).first()

def getNodeData(node_id):
    return NodeData.query.filter(NodeData.node_id==node_id).all()



def getResultLogs(node, timestamp, action):
    return node.result_logs.filter(ResultLog.timestamp > timestamp, ResultLog.action != action).all()

def getResultLogsByQuerName(node, timestamp, action, query_name):
    return node.result_logs.filter(ResultLog.timestamp > timestamp, ResultLog.action != 'removed',
                                                ResultLog.name == query_name)

def getResultLogsOffsetLimit(node, timestamp, action, query_name, start, limit):
    return node.result_logs.filter(ResultLog.timestamp > timestamp,
                                                        ResultLog.action != action,
                                                        ResultLog.name == query_name).offset(start).limit(limit)

def extend_nodes_by_node_key_list(nodeKeyList):
    return Node.query.filter(or_(
                        Node.node_key.in_(nodeKeyList), Node.host_identifier.in_(nodeKeyList))).all()

def extend_nodes_by_tag(tags):
    return Node.query.filter(
                        Node.tags.any(
                            Tag.value.in_(tags))).all()

def getResultLogsByHostId(node, timestamp, query_name):
    return node.result_logs.filter(ResultLog.timestamp > timestamp, ResultLog.action != 'removed', ResultLog.name == query_name)


def engineQuery(node_data_str):
    return db.session.execute(text(node_data_str))

def queryStrList(name, node_id, searchColumn, searchTerm):
    return db.session.query(ResultLog.columns) \
                .filter(ResultLog.name == name) \
                .filter(ResultLog.node_id == int(node_id)) \
                .filter(
                ResultLog.columns[searchColumn].astext.ilike("%" + searchTerm + "%")
            )


def resultLogNamesQuery(node_id):
    return db.session.query(
            ResultLog.name).distinct(ResultLog.name). \
            filter(ResultLog.node_id == node_id). \
            all()


def nodeActivityQuery(node_id):
    return Node.query.filter_by(id=node_id) \
            .options(db.lazyload('*')).first()



def filterNodesByStateActivity(platform = None, state = None):
    checkin_interval = current_app.config['POLYLOGYX_CHECKIN_INTERVAL']
    current_time = dt.datetime.utcnow() - checkin_interval

    if (not platform) and state==None:
        return get_all_nodes()
    elif state == None:
        return Node.query.filter_by(platform=platform).all()
    elif not platform:
        if state: return Node.query.filter(Node.is_active==state, Node.last_checkin > current_time).all()
        else: return Node.query.filter(Node.is_active==state, Node.last_checkin < current_time).all()
    else:
        return Node.query.filter(Node.platform==platform, Node.is_active==state, Node.last_checkin < current_time).all()

def node_result_log_search_results(filter,node_id):
    return db.session.query(ResultLog.node_id,ResultLog.name,ResultLog.columns).filter(*filter).filter(ResultLog.node_id == node_id).all()