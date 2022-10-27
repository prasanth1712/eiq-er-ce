import json, sqlalchemy, os, six
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from functools import wraps
import datetime as dt
from operator import and_

from flask import jsonify, current_app, request, abort
from flask_restful import reqparse

from polylogyx.models import Node, Settings, db, ResultLog
from polylogyx.dao.v1 import hosts_dao as node_dao
from polylogyx.search_rules import AndCondition, OrCondition, BaseCondition, OPERATOR_MAP

"""Common utils/ all methods used in blueprints folder will be defined here"""


def tag_name_format(Tags):
    """used in packs queries nodes"""
    data = [tag.to_dict() for tag in Tags]
    return data


def get_body_data(request):
    return json.loads(request.data)


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    # return datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
    return value.strftime("%Y-%m-%d") + ' ' + value.strftime("%H:%M:%S")


def validate_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.data:
            response = {}
            response['status'] = 'failure'
            response['message'] = 'Data missing'
            return jsonify(response)
        else:
            try:
                request.data = json.loads(request.data)
                return f(*args, **kwargs)
            except:
                current_app.logger.error("%s - Invalid data", request.remote_addr)
                abort(400)

        return f(*args, **kwargs)

    return decorated_function


def validate_command(request_data):
    response = {}
    types = ['file', 'process']
    status = 'failure'
    message = 'Invalid Data'

    for type in types:
        try:
            if request_data.get('target').get(type):

                node = Node.query.filter(
                    Node.host_identifier == request_data.get('target').get(type).get(
                        'device').get(
                        'hostname')).first()
                if node: return True, node
        except:
            status = 'failure'
            message = 'Please provide a valid command'

    response['status'] = status
    response['message'] = message
    return False, jsonify(response)


def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


def save_or_update_setting(setting, v, k):
    if setting:
        setting.setting = v
        setting.update(setting)
    else:
        Settings.create(name=k, setting=v)


def json_serial(obj):
    if isinstance(obj, (dt.datetime, dt.date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


# request parsing function
def requestparse(args_to_add, type_list, help_list, required=None):
    """function which parse the request body data into dictionary"""
    if not required: required = [True for i in args_to_add]
    parser = reqparse.RequestParser()
    if not 'file' in args_to_add:
        for i in range(len(args_to_add)):
            parser.add_argument(args_to_add[i], type=type_list[i], help=help_list[i], required=required[i])
    else:
        for i in range(len(args_to_add)):
            if not args_to_add[i] == 'file':
                parser.add_argument(args_to_add[i], type=type_list[i], help=help_list[i], required=required[i])
            else:
                parser.add_argument(args_to_add[i], type=type_list[i], help=help_list[i], required=required[i],
                                    location='files')
    return parser


def prepare_response(message, status=None, data=None):
    """returns a response dictionary needed to apply to wrappers"""
    if status and data:
        return {'message': message, 'status': status, 'data': data}
    elif status:
        return {'message': message, 'status': status}
    else:
        return {'message': message}


def send_alert(node, rule_match, intel_match):
    from polylogyx.models import current_app as app
    from polylogyx.plugins import AbstractAlerterPlugin
    alerters = app.config.get('POLYLOGYX_ALERTER_PLUGINS', {})

    for name, (plugin, config) in alerters.items():
        package, classname = plugin.rsplit('.', 1)
        from importlib import import_module
        module = import_module(package)
        klass = getattr(module, classname, None)

        if klass is None:
            raise ValueError('Could not find a class named "{0}" in package "{1}"'.format(classname, package))

        if not issubclass(klass, AbstractAlerterPlugin):
            raise ValueError('{0} is not a subclass of AbstractAlerterPlugin'.format(name))
        alerter_obj = klass(config)

        try:
            alerter_obj.handle_alert(node, rule_match, intel_match)
            return True
        except Exception as e:
            current_app.logger.error(e)
            return False


def add_pack_through_json_data(args):
    from polylogyx.dao.v1 import packs_dao, queries_dao
    from polylogyx.wrappers.v1 import parent_wrappers
    from polylogyx.utils import create_tags, validate_osquery_query
    from flask_restful import marshal

    if 'tags' in args:
        tags = args['tags'].split(',')
    else:
        tags = []
    name = args['name']
    queries = args['queries']
    pack = packs_dao.get_pack_by_name(name)
    if not pack:
        pack = packs_dao.add_pack(**args)

    for query_name, query in queries.items():
        if not validate_osquery_query(query['query']):
            message = ('Invalid osquery query: "{0}"'.format(query['query']))
            return marshal({'message': message}, parent_wrappers.failure_response_parent)
        q = queries_dao.get_query_by_name(query_name)

        if not q:
            q = queries_dao.add_query(query_name, **query)
            pack.queries.append(q)
            current_app.logger.debug("Adding new query %s to pack %s",
                                     q.name, pack.name)
            continue
        else:
            if q.sql == query['query']:
                current_app.logger.debug("Adding existing query %s to pack %s",
                                         q.name, pack.name)
                pack.queries.append(q)
            else:
                q2 = queries_dao.add_query(query_name, **query)
                current_app.logger.debug(
                    "Created another query named %s, but different sql: %r vs %r",
                    query_name, q2.sql.encode('utf-8'), q.sql.encode('utf-8'))
                pack.queries.append(q2)

        if q in pack.queries:
            continue

    if pack:
        if tags:
            pack.tags = create_tags(*tags)
        pack.save()
    return pack


def get_node_id_by_host_id(host_identifier):
    node = node_dao.get_node_by_host_identifier(host_identifier)
    if node:
        return node.id


def get_host_id_by_node_id(node_id):
    node = node_dao.get_node_by_id(node_id)
    if node:
        return node.host_identifier


def get_queries_or_packs_of_node(node_id):
    return db.session.query(
        ResultLog.name).distinct(ResultLog.name). \
        filter(ResultLog.node_id == (node_id)). \
        all()


def get_results_by_query(startPage, perPageRecords, node_id, name, args=None):
    searchTerm = None
    columns = []
    columnsDefined = False
    try:
        startPage = int(args['start'])
        perPageRecords = int(args['length'])
        if 'search[value]' in args and (args['search[value]'] != ""):
            searchTerm = (args['search[value]'])
        if (args['columns[0][data]']):
            columnsDefined = True
    except:
        print('error in request')
    results = []
    count = db.session.query(ResultLog).filter(
        and_(ResultLog.name == name, and_(ResultLog.node_id == node_id, ResultLog.action != 'removed'))).count()
    countFiltered = count

    if searchTerm:
        queryCountStr = "select count(distinct id) from result_log join jsonb_each_text(result_log.columns) e on true where  node_id='" + str(
            node_id) + "' and e.value ilike " + "'%" + searchTerm + "%'" + " and name=" + "'" + name + "'" + " and action!='removed'"

        filtered_quer = db.session.execute(sqlalchemy.text(queryCountStr))
        for r in filtered_quer:
            countFiltered = r[0]

        queryStr = "select distinct id,columns from result_log join jsonb_each_text(result_log.columns) e on true where  node_id='" + str(
            node_id) + "' and e.value ilike " + "'%" + searchTerm + "%'" + " and name=" + "'" + name + "'" + " and action!='removed' order by id desc OFFSET " + str(
            startPage) + "  LIMIT " + str(perPageRecords)
        record_query = db.session.execute(sqlalchemy.text(queryStr))
        for r in record_query:
            results.append(r[1])

    else:
        record_query = db.session.query(ResultLog.columns).filter(
            and_(ResultLog.node_id == (node_id), and_(ResultLog.name == name, ResultLog.action != 'removed'))).order_by(
            sqlalchemy.desc(ResultLog.id)).offset(
            startPage).limit(
            perPageRecords).all()
        results = [r for r, in record_query]

        if results:
            firstRecord = results[0]

            TO_CAPTURE_COlUMNS = []
            if 'action' in firstRecord:
                if 'PROC_' in firstRecord['action']:
                    TO_CAPTURE_COlUMNS = ['utc_time', 'action', 'path', 'parent_path']
                elif 'Close' in firstRecord['action'] or 'Accept' in firstRecord['action'] or 'Connect' in firstRecord[
                    'action']:
                    TO_CAPTURE_COlUMNS = ['utc_time', 'action', 'process_name', 'protocol', 'local_address',
                                          'local_port', 'remote_address' 'remote_port']
                elif 'DELETE' in firstRecord['action'] or 'READ' in firstRecord['action'] or 'WRITE' in firstRecord[
                    'action']:
                    TO_CAPTURE_COlUMNS = ['utc_time', 'action', 'process_name', 'md5', 'target_path']

            elif 'event_type' in firstRecord:
                if 'dns_req' == firstRecord['event_type'] or 'dns_res' == firstRecord['event_type']:
                    TO_CAPTURE_COlUMNS = ['domain_name', 'resolved_ip', 'utc_time', 'request_type', 'request_class']
                elif 'http_req' == firstRecord['event_type']:
                    TO_CAPTURE_COlUMNS = ['utc_time', 'url', 'remote_port', 'process_name']

            if len(TO_CAPTURE_COlUMNS) == 0:
                for key in firstRecord.keys():
                    columns.append({'data': key, 'title': key})
            else:
                columns.append({"className": 'details-control',
                                "orderable": False,
                                "data": None,
                                "defaultContent": ''})
                for key in firstRecord.keys():
                    if key in TO_CAPTURE_COlUMNS:
                        columns.append({'data': key, 'title': key})

    output = {}
    try:
        output['sEcho'] = str(int(request.values['sEcho']))
    except:
        print('error in echo')
    output['iRecordsFiltered'] = str(countFiltered)
    output['iTotalRecords'] = str(count)
    output['pageLength'] = str(perPageRecords)

    output['iTotalDisplayRecords'] = str(countFiltered)
    aaData_rows = results

    # add additional rows here that are not represented in the database
    # aaData_row.append(("""""" % (str(row[ self.index ]))).replace('\\', ''))
    if not columnsDefined:
        output['columns'] = columns
    output['aaData'] = aaData_rows
    db.session.commit()
    return output


def parse_condition(d):
    op = d['operator']
    value = d['value']

    # If this is a "column operator" - i.e. operating on a particular
    # value in a column - then we need to give a custom extraction
    # function that knows how to get this value from a query.
    column_name = None
    if d['field'] == 'column':
        # Strip 'column_' prefix to get the 'real' operator.
        op = op[7:]
        if isinstance(value, six.string_types):
            column_name = value
        else:
            # The 'value' array will look like ['column_name', 'actual value']
            column_name, value = value

    klass = OPERATOR_MAP.get(op)
    if not klass:
        raise ValueError("Unsupported operator: {0}".format(op))

    inst = make_condition(klass, d['field'], value, column_name=column_name)
    return inst


def parse_group(d):
    if len(d['rules']) == 0:
        raise ValueError("A group contains no rules")
    upstreams = [parse(r) for r in d['rules']]
    condition = d['condition']
    if condition == 'AND':
        return make_condition(AndCondition, upstreams)
    elif condition == 'OR':
        return make_condition(OrCondition, upstreams)

    raise ValueError("Unknown condition: {0}".format(condition))


def parse(d):
    if 'condition' in d:
        return parse_group(d)
    return parse_condition(d)


def make_condition(klass, *args, **kwargs):
    """
    Memoizing constructor for conditions.  Uses the input config as the cache key.
    """
    conditions = {}
    alert_conditions = []

    # Calculate the memoization key.  We do this by creating a 3-tuple of
    # (condition class name, args, kwargs).  There is some nuance to this,
    # though: we need to put args/kwargs in the right format.  We
    # recursively iterate through lists/dicts and convert them to tuples,
    # and extract the memoization key from instances of BaseCondition.
    def tupleify(obj):
        if isinstance(obj, BaseCondition):
            return obj.__network_memo_key
        elif isinstance(obj, tuple):
            return tuple(tupleify(x) for x in obj)
        elif isinstance(obj, list):
            return tuple(tupleify(x) for x in obj)
        elif isinstance(obj, dict):
            items = ((tupleify(k), tupleify(v)) for k, v in obj.items())
            return tuple(sorted(items))
        else:
            return obj

    args_tuple = tupleify(args)
    kwargs_tuple = tupleify(kwargs)

    key = (klass.__name__, args_tuple, kwargs_tuple)
    if key in conditions:
        return conditions[key]

    # Instantiate the condition class.  Also, save the memoization key on
    # the class, so it can be retrieved (above).
    inst = klass(*args, **kwargs)
    inst.__network_memo_key = key

    # Save the condition
    conditions[key] = inst
    return inst


def add_rule_name_to_alerts_response(dictionary_list_data):
    from polylogyx.dao.v1 import rules_dao
    for dict_item in dictionary_list_data:
        if dict_item['type'] == 'rule':
            if 'rule_name' not in dict_item:
                rule = rules_dao.get_rule_name_by_id(dict_item['rule_id'])
                if rule:
                    dict_item['rule_name'] = rule.name
            return dictionary_list_data
