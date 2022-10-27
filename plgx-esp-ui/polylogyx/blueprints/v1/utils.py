import six,re
import datetime as dt
import unicodecsv as csv
from io import BytesIO
from flask import current_app, send_file,request,abort
from flask_restful import reqparse,marshal
from polylogyx.models import Node, Rule, Alerts, db, Settings,Query
from polylogyx.dao.v1 import rules_dao, packs_dao, alerts_dao, hosts_dao, queries_dao, dashboard_dao ,users_dao
from polylogyx.util.constants import DEFAULT_EVENT_STATE_QUERIES
from polylogyx.constants import PolyLogyxServerDefaults
from functools import wraps


process_guid_column = 'process_guid'
parent_process_guid_column = 'parent_process_guid'


def requestparse(args_to_add, type_list, help_list, required=None, choices=None, default=None, nullable_list=None):
    """
    function which parses the request body data into dictionary
    """
    if not required:
        required = [True for i in args_to_add]
    if not choices:
        choices = [None for i in args_to_add]
    if not default:
        default = [None for i in args_to_add]
    if not nullable_list:
        nullable_list = [None for i in args_to_add]

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('x-access-token', location='headers', type=str, help="JWT Access token(From Login API)",
                        required=True)
    for i in range(len(args_to_add)):
        if required[i]:
            nullable = False
            if nullable_list[i]:
                nullable = True
        else:
            nullable = True
        if not args_to_add[i] == 'file':
            if type_list[i] == list:
                parser.add_argument(args_to_add[i], action='append', help=help_list[i], required=required[i],
                                    choices=choices[i], default=default[i], nullable=nullable)
            else:
                parser.add_argument(args_to_add[i], type=type_list[i], help=help_list[i], required=required[i],
                                    choices=choices[i], default=default[i], nullable=nullable)
        else:
            if type_list[i] == list:
                parser.add_argument(args_to_add[i], action='append', help=help_list[i], required=required[i],
                                    location='files', nullable=nullable)
            else:
                parser.add_argument(args_to_add[i], type=type_list[i], help=help_list[i], required=required[i],
                                    location='files', nullable=nullable)
    return parser


def prepare_response(message, status=None, data=None):
    """
    returns a response dictionary needed to apply to wrappers
    """
    if status is not None and data is not None:
        return {'message': message, 'status': status, 'data': data}
    elif status is not None:
        return {'message': message, 'status': status}
    else:
        return {'message': message}


def add_pack_through_json_data(args):
    from polylogyx.utils import create_tags, validate_osquery_query
    from polylogyx.models import Pack

    if 'tags' in args and args['tags']:
        tags = args['tags'].split(',')
    else:
        tags = []
    name = args['name']
    queries = args['queries']
    category = args.get('category', Pack.GENERAL)
    platform = args.get('platform', None)
    version = args.get('version', None)
    description = args.get('description', None)
    shard = args.get('shard', None)

    pack = packs_dao.get_pack_by_name(name)
    if not pack:
        pack = packs_dao.add_pack(name, category, platform, version, description, shard)
        for query_name, query in queries.items():
            if not 'platform' in query:
                query['platform'] = 'all'
            if validate_osquery_query(query['query']):
                q = queries_dao.add_query(query_name, **query)
                pack.queries.append(q)
                current_app.logger.debug("Adding new query %s to pack %s",
                                         q.name, pack.name)
    else:
        pack = pack.update(category=category,platform=platform,version=version,description=description, shard=shard)
        pack_queries = {query.name:query for query in pack.queries}
        for query_name, query in queries.items():
            if not 'platform' in query:
                query['platform'] = 'all'
            if validate_osquery_query(query['query']) and query_name not in pack_queries:
                q2 = queries_dao.add_query(query_name, **query)
                current_app.logger.debug("Created another query named %s, but different sql: %r vs %r", query_name, q2.sql.encode('utf-8'), q2.sql.encode('utf-8'))
                pack.queries.append(q2)
    if pack:
        if tags:
            pack.tags = create_tags(*tags)
        pack.save()
    return pack


def get_node_id_by_host_id(host_identifier):
    node = hosts_dao.get_node_by_host_identifier(host_identifier)
    if node:
        return node.id


def get_host_id_by_node_id(node_id):
    node = hosts_dao.get_node_by_id(node_id)
    if node:
        return node.host_identifier


def get_nodes_for_host_id(host_identifier):
    return Node.query.filter(Node.host_identifier == host_identifier).all()


class UnSupportedSearchColumn(Exception):
    pass


class RuleParser:

    def parse_condition(self, d):
        from polylogyx.rules import OPERATOR_MAP

        op = d['operator']
        value = d['value']

        # If this is a "column operator" - i.e. operating on a particular
        # value in a column - then we need to give a custom extraction
        # function that knows how to get this value from a query.
        if value == "":
            raise ValueError("Value should be provided!")
        column_name = None
        if d['field'] == 'column':
            # Strip 'column_' prefix to get the 'real' operator.
            if op.startswith('column_'):
                op = op[7:]
            if isinstance(value, six.string_types):
                column_name = value
            else:
                # The 'value' array will look like ['column_name', 'actual value']
                column_name, value = value
        klass = OPERATOR_MAP.get(op)
        if not klass:
            raise ValueError("Unsupported operator: {0}".format(op))

        inst = self.make_condition(klass, d['field'], value, column_name=column_name)
        return inst

    def parse_group(self, d):
        from polylogyx.rules import AndCondition, OrCondition

        if len(d['rules']) == 0:
            raise ValueError("A group contains no rules")
        upstreams = [self.parse(r) for r in d['rules']]
        condition = d['condition']
        if condition == 'AND' or condition == 'and':
            return self.make_condition(AndCondition, upstreams)
        elif condition == 'OR' or condition == 'or':
            return self.make_condition(OrCondition, upstreams)

        raise ValueError("Unknown condition: {0}".format(condition))

    def parse(self, d):
        if 'condition' in d:
            return self.parse_group(d)
        return self.parse_condition(d)

    def make_condition(self, klass, *args, **kwargs):
        from polylogyx.rules import BaseCondition

        """
        Memoizing constructor for conditions.  Uses the input config as the cache key.
        """
        conditions = {}

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


class SearchParser:

    def parse_condition(self, d):
        from polylogyx.search_rules import OPERATOR_MAP

        op = d['operator']
        value = d['value']
        # If this is a "column operator" - i.e. operating on a particular
        # value in a column - then we need to give a custom extraction
        # function that knows how to get this value from a query.
        if value == "":
            raise ValueError("Value should be provided!")
        column_name = None
        if d['field'] == 'column':
            # Strip 'column_' prefix to get the 'real' operator.
            if op.startswith('column_'):
                op = op[7:]
            if isinstance(value, six.string_types):
                column_name = value
            else:
                # The 'value' array will look like ['column_name', 'actual value']
                column_name, value = value
        if not column_name:
            column_name = d['field']
        klass = OPERATOR_MAP.get(op)

        if not klass:
            raise ValueError("Unsupported operator: {0}".format(op))

        if column_name not in PolyLogyxServerDefaults.search_supporting_columns:
            raise UnSupportedSearchColumn("Unsupported column '{}'".format(column_name))

        inst = self.make_condition(klass, d['field'], value, column_name=column_name)
        return inst

    def parse_group(self, d):
        from polylogyx.search_rules import AndCondition, OrCondition

        if len(d['rules']) == 0:
            raise ValueError("A group contains no rules")
        upstreams = [self.parse(r) for r in d['rules']]
        condition = d['condition']
        if condition == 'AND' or condition == 'and':
            return self.make_condition(AndCondition, upstreams)
        elif condition == 'OR' or condition == 'or':
            return self.make_condition(OrCondition, upstreams)

        raise ValueError("Unknown condition: {0}".format(condition))

    def parse(self, d):
        if 'condition' in d:
            return self.parse_group(d)
        return self.parse_condition(d)

    def make_condition(self, klass, *args, **kwargs):
        from polylogyx.search_rules import BaseCondition

        """
        Memoizing constructor for conditions.  Uses the input config as the cache key.
        """
        conditions = {}

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


def get_response(results):
    from polylogyx.wrappers.v1 import parent_wrappers
    if results:
        firstRecord = results[0]
        headers = []
        for key in firstRecord.keys():
            headers.append(key)

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerow(headers)

        for data in results:
            row = []
            row.extend([data.get(column) for column in headers])
            writer.writerow(row)

        bio.seek(0)

        response = send_file(
            bio,
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename='alert_source_results.csv'
        )
        response.direct_passthrough = False
        return response
    else:
        return marshal(prepare_response("Data couldn't find for the alert source given!", "failure"),
                       parent_wrappers.common_response_wrapper)


def add_rule_name_to_alerts_response(dictionary_list_data):
    from polylogyx.dao.v1 import rules_dao
    for dict_item in dictionary_list_data:
        if dict_item['type'] == 'rule':
            if 'rule_name' not in dict_item:
                rule = rules_dao.get_rule_name_by_id(dict_item['rule_id'])
                if rule:
                    dict_item['rule_name'] = rule.name
    return dictionary_list_data


def fetch_alert_node_query_status():
    limits = 5
    rules = dashboard_dao.get_rules_data(limits)
    nodes = dashboard_dao.get_host_data(limits)
    queries = dashboard_dao.get_queries(limits)

    alerts = {}
    top_five_alerts = {}

    # rules count
    rule = []
    for row_list in rules:
        rule_ele = {'rule_id':row_list[0],'rule_name': row_list[1], 'count': row_list[2]}
        rule.append(rule_ele)
    top_five_alerts['rule'] = rule

    # host count
    hosts = []
    for row_list in nodes:
        host_ele = {'host_id':row_list[0],'host_identifier': row_list[1], 'host_name': row_list[2], 'count': row_list[3]}
        hosts.append(host_ele)
    top_five_alerts['hosts'] = hosts

    # queries count
    query = []
    for row_list in queries:
        query_ele = {'query_name': row_list[0], 'count': row_list[1]}
        query.append(query_ele)
    top_five_alerts['query'] = query
    alerts['top_five'] = top_five_alerts

    # fetching alerts count by severity and type
    alert_count = dashboard_dao.get_alert_count()

    alert_name = {
        'ioc': {'INFO': 0, 'LOW': 0, 'MEDIUM': 0, 'CRITICAL': 0,'HIGH':0,'INFO':0},
        'rule': {'INFO': 0, 'LOW': 0, 'MEDIUM': 0, 'CRITICAL': 0,'HIGH':0,'INFO':0},
        'virustotal': {'INFO': 0, 'LOW': 0, 'MEDIUM': 0, 'CRITICAL': 0,'HIGH':0,'INFO':0},
        'ibmxforce': {'INFO': 0, 'LOW': 0, 'MEDIUM': 0, 'CRITICAL': 0,'HIGH':0,'INFO':0},
        'alienvault': {'INFO': 0, 'LOW': 0, 'MEDIUM': 0, 'CRITICAL': 0,'HIGH':0,'INFO':0}
    }
    for alert in alert_count:
        alert_name[alert[0]][alert[1]] = alert[2]

    for key in alert_name.keys():
        alert_name[key]['TOTAL'] = alert_name[key]['INFO'] + alert_name[key]['LOW'] + alert_name[key]['MEDIUM'] + \
                                   alert_name[key]['CRITICAL']+alert_name[key]['HIGH']

    alerts['source'] = alert_name

    return alerts


def fetch_dashboard_data():
    distribution_and_status = {}
    #counts = dashboard_dao.get_platform_count()
    counts = hosts_dao.get_platform_count()
    distribution_and_status['hosts_platform_count'] = counts

    checkin_interval = current_app.config['POLYLOGYX_CHECKIN_INTERVAL']
    current_time = dt.datetime.utcnow() - checkin_interval
    online_nodes = dashboard_dao.get_online_node_count(current_time)
    offline_nodes = dashboard_dao.get_offline_node_count(current_time)

    distribution_and_status['hosts_status_count'] = {'online': online_nodes, 'offline': offline_nodes}

    return distribution_and_status


def get_alerts_data(source, start_date, end_date, node, rule_id,severity=None,verdict=None,search=None):
    try:
        data = []
        alerts_severity = alerts_dao.get_alerts_severity_with_id_timestamp(source, start_date, end_date, node, rule_id,severity,verdict,search)

        for alert in alerts_severity:
            color = ""
            if alert[1]:
                if alert[1] == Rule.MEDIUM:
                    color = "green-m"
                elif alert[1] == Rule.INFO:
                    color = ""
                elif alert[1] == Rule.CRITICAL:
                    color = "yellow"
                elif alert[1] == Rule.HIGH:
                    color = "orange"
                elif alert[1] == Rule.LOW:
                    color = "green"
            data.append({"start": alert[2].timestamp() * 1000, "content": "",
                         "event_id": alert[0], "className": color})
        return data
    except Exception as e:
        print(e, 'error in request')


def get_results_by_alert_source(start, limit, source, searchterm="", resolved=None, event_ids=None, start_date=None,
                                end_date=None, node_id=None, query_name=None, rule_id=None, events_count=False,column=None,order_by=None,severity=None,verdict=None):
    """ Alerts by source Result Set. """

    if resolved == True:
        filter = alerts_dao.resolved_alert()
    elif resolved == False:
        filter = alerts_dao.non_resolved_alert()
    else:
        filter=None

    base_query = alerts_dao.get_record_query_by_dsc_order(filter, source, searchterm, event_ids, node_id, query_name, rule_id, events_count,column,order_by,severity,verdict)

    if not resolved and start_date and end_date:
        base_query = base_query.filter(Alerts.created_at >= start_date).filter(Alerts.created_at <= end_date)

    count = base_query.count()

    total_count = alerts_dao.get_record_query_total_count(filter, source, node_id, query_name, rule_id)
    record_query = base_query.offset(start).limit(limit).all()
    alerts = []
    for alert_log_pair in record_query:
        if events_count:
            alert = alert_log_pair[0].as_dict()
            alert['aggregated_events_count'] = alert_log_pair[1]
        else:
            alert = alert_log_pair.as_dict()
        alert['alerted_entry'] = alert.pop('message')
        alert['intel_data'] = alert.pop('source_data')
        alert['hostname'] = hosts_dao.get_all_nodes_by_id(alert['node_id']).display_name

        if alert['source'] == 'rule':
            rule=rules_dao.get_rule_name_by_id(alert['rule_id'])
            alert['rule'] = {'name':rule.name ,'id': alert['rule_id'],'status':rule.status}
            del alert['intel_data']
        elif source == 'self' or source == 'IOC' or source == 'ioc':
            del alert['rule_id']
            del alert['intel_data']
            if 'rule' in alert:
                del alert['rule']
        else:
            del alert['rule_id']
            if 'rule' in alert:
                del alert['rule']
        alerts.append(alert)

    output = {'count': count, 'total_count': total_count, 'results': alerts}
    return output


def get_node_data_by_action_and_pid(action, process_guid, host_id, eid, last_time, alert):
    process_guid_column_name = process_guid_column
    if action and 'PROC_CREATE' in action:
        process_guid_column_name = parent_process_guid_column
    child_action_nodes = alerts_dao.get_child_action_node(
        process_guid_column_name, process_guid, action, host_id, eid, last_time)
    if alert and process_guid_column_name in alert.message and process_guid == alert.message[process_guid_column_name]:
        child_action_nodes.append([alert.message])

    hosts = []
    process_guid_count = {}
    if action and 'PROC_CREATE' in action:
        process_guids = []
        for child_action_node in child_action_nodes:
            process_guids.append(child_action_node[0][process_guid_column])
        process_guid_count = check_if_process_has_child(process_guids, host_id)

    for child_action_node in child_action_nodes:
        host = {}
        host["color"] = 'red'
        host["name"] = "child"
        host["data"] = child_action_node[0]
        last_time = child_action_node[0]['time']
        if action and 'PROC_CREATE' in action and host['data'][process_guid_column] in process_guid_count:
            host['has_child'] = True

        hosts.append(host)

    return hosts, last_time


def check_if_process_has_child(process_guids, host_id):
    process_guid_count = {}
    child_action_counts = alerts_dao.get_child_action_count(process_guids, host_id)

    child_process_counts = alerts_dao.get_child_process_count(process_guids, host_id)

    for child_action_count in child_action_counts:
        if (child_action_count[1]) > 0:
            process_guid_count[child_action_count[0]] = True
    for child_process_count in child_process_counts:
        if (child_process_count[1]) > 0:
            process_guid_count[child_process_count[0]] = True
    return process_guid_count


def time_in_alert(alert):
    try:
        if 'time' in alert.message:
            time = alert.message['time']
            time = int(time)
            return time
    except Exception as e:
        print(e)


def alerts_details(alert,platform_activity=None):
    from polylogyx.wrappers.v1.alert_wrappers import alerts_wrapper
    alerts_data = marshal(alert, alerts_wrapper)
    if alerts_data['source'] == 'rule':
        rule=rules_dao.get_rule_name_by_id(alerts_data['rule_id'])
        if rule:
            alerts_data['rule'] = {
                                    'name':rule.name,
                                    'id': alerts_data['rule_id'],
                                    'status':rule.status
                                  }
    if int(alerts_data['verdict']) == 2:
        alerts_data['verdict'] = 'FALSE POSITIVE'
    elif int(alerts_data['verdict']) == 1:
        alerts_data['verdict'] = 'TRUE POSITIVE'
    else:
        alerts_data['verdict'] = None
    host = hosts_dao.get_node_by_id(alerts_data['node_id'])
    alerts_data['hostname'] = host.display_name
    alerts_data['platform'] = host.platform
    alerts_data['updated_by'] = None
    if platform_activity:
        alerts_data['updated_by'] = platform_activity.user.username
    return alerts_data


def get_alert_system_details(alert):
    time = 0
    platform = get_platform(alert)

    SYSTEM_STATE_QUERIES = DEFAULT_EVENT_STATE_QUERIES[platform]['state_queries']
    SYSTEM_EVENT_QUERIES = DEFAULT_EVENT_STATE_QUERIES[platform]['event_queries']

    system_state_data_event_list = [query_ele[0] for query_ele in
                                    alerts_dao.get_system_event_data_list(SYSTEM_STATE_QUERIES, alert)]
    schedule_query = schedule_query_data_by_time(alert, SYSTEM_EVENT_QUERIES)
    data = {
        "schedule_query_data_list_obj": schedule_query,
        "system_state_data_list": system_state_data_event_list,
    }
    return data


def get_host_state_query_count(alert):
    platform = get_platform(alert)
    state_queries = DEFAULT_EVENT_STATE_QUERIES[platform]['state_queries']
    return [{"query_name": query_ele[0], "count": query_ele[1]} for query_ele in
            alerts_dao.get_system_state_data_list(state_queries, alert)]


def get_platform(alert):
    platform = alert.node.platform
    if platform not in ['windows', 'freebsd', 'darwin']:
        platform = 'linux'
    return platform


def schedule_query_data_by_time(alert, SYSTEM_EVENT_QUERIES):
    time = time_in_alert(alert)
    if time:
        schedule_query_data = alerts_dao.get_schedule_query_data(
            SYSTEM_EVENT_QUERIES, alert, time)

        schedule_query_data_list = []
        schedule_query_data_obj = {}
        for r in schedule_query_data:
            if not r[0] in schedule_query_data_obj:
                schedule_query_data_obj[r[0]] = []
            if 'time' in r[1]:
                utc_time = dt.datetime.utcfromtimestamp(int(r[1]['time']))
                r[1].update({'date': utc_time.strftime('%a %b %d %H:%M:%S %Y') + " UTC"})
                schedule_query_data_obj[r[0]].append(r[1])
            elif 'utc_time' in r[1]:
                r[1].update({'date': r[1]['utc_time'].replace('\n', ' UTC')})
                schedule_query_data_obj[r[0]].append(r[1])

        for name, array in schedule_query_data_obj.items():
            schedule_query_data_list.append({"name": name, "data": array})
        return schedule_query_data_list
    return


def unwrap_alert_message(alert):
    eid = None
    alerted_process_guid = None
    alerted_process_name = None
    if 'eid' in alert.message:
        eid = alert.message.get('eid')
    if 'parent_process_guid' in alert.message:
        alerted_process_guid = alert.message.get('parent_process_guid')
    elif 'process_guid' in alert.message:
        alerted_process_guid = alert.message.get('process_guid')
    if 'parent_path' in alert.message:
        alerted_process_name = alert.message.get('parent_path')
    elif 'process_name' in alert.message:
        alerted_process_name = alert.message.get('process_name')
    alerted_action = alert.message.get('action')
    return eid, alerted_process_guid, alerted_process_name, alerted_action


def graph_data_based_on_process(process_guid, node_id, alert):
    process_name = process_guid
    child_action_nodes = alerts_dao.get_child_action_node_by_process_guid(node_id, process_guid)
    node_graph_action_data = []
    node = {"name": process_guid, "data": {'process_guid': process_guid, 'path': process_guid}}
    if alert and alert.message:
        eid, alerted_process_guid, alerted_process_name, alerted_action = unwrap_alert_message(alert)
    for child_action_node in child_action_nodes:
        if alert and alert.message and alerted_action == child_action_node[0] and alerted_process_guid == process_guid:
            if alerted_process_name:
                process_name = alerted_process_name
            node['name'] = process_name
            node['data'] = {'process_guid': process_guid, 'path': process_name}

            alerted_proc_create = alerts_dao.get_alerted_proc_create(process_guid, node_id)
            if alerted_proc_create:
                alerted_proc_data = alerted_proc_create[0]
                node['action'] = 'PROC_CREATE'
                node['node_type'] = 'root'
                node['name'] = alerted_proc_data['path']
                node["data"] = alerted_proc_data
            children, last_time = get_node_data_by_action_and_pid(alerted_action, process_guid,
                                                                  node_id, eid, None, alert)

            node_graph_action_data.append({
                "action": child_action_node[0],
                "count": child_action_node[1],
                "color": 'blue',
                'node_type': 'action',
                "children": children,
                'last_time': last_time,
                "all_children": children,
                "name": child_action_node[0],
                "fetched": True,
                'process_guid': process_guid,
            })
        else:
            node_graph_action_data.append({
                "action": child_action_node[0],
                "count": child_action_node[1],
                "color": 'blue',
                'node_type': 'action',
                "name": child_action_node[0],
                'process_guid': process_guid,
            })

    graph_data = {"name": node["name"].split('\\')[-1], "path": node["name"],
                  "all_children": node_graph_action_data}
    if alert and alert.message and alerted_process_guid == process_guid:
        graph_data['node_type'] = 'root'
    if "data" in node:
        graph_data["data"] = node["data"]
    return graph_data


def get_start_date_end_date(args):
    end_date = dt.datetime.utcnow()
    end_date = dt.datetime.strptime(end_date.today().strftime('%Y-%m-%d'), '%Y-%m-%d')+dt.timedelta(days=1)
    start_date = dt.datetime.strptime(end_date.today().strftime('%Y-%m-%d'), '%Y-%m-%d') - dt.timedelta(weeks=1)+dt.timedelta(days=1)
    type = args['type']
    duration = args['duration']
    if 'date' in args and args['date']:
        date = dt.datetime.strptime(args['date'], '%Y-%m-%d')
        difference_time = 0
        if duration == 1:
            difference_time = dt.timedelta(hours=1)
        elif duration == 2:
            difference_time = dt.timedelta(days=1)
        elif duration == 3:
            difference_time = dt.timedelta(weeks=1)
        elif duration == 4:
            difference_time = dt.timedelta(days=30)
        if type == 1:
            start_date = date
            end_date = start_date + difference_time
        elif type == 2:
            end_date = date
            start_date = end_date - difference_time
    if 'start_date' in args and args['start_date']:
        start_date = dt.datetime.strptime(args['start_date'], '%Y-%m-%d')

        if 'end_date' in args and args['end_date']:
            end_date =  dt.datetime.strptime(args['end_date'], '%Y-%m-%d')
        return start_date,end_date+dt.timedelta(days=1)
    return start_date+dt.timedelta(days=1), end_date+dt.timedelta(days=1)


def result_log_columns_export_using_query_set(results):
    headers = []
    data_array = []
    if not len(results) == 0:
        headers = list(results[0].keys())
    for data in results:
        row = []
        for key in data.keys():
            if key not in headers:
                headers.append(key)
        row.extend([data.get(column, '') for column in headers])
        data_array.append(row)

    bio = BytesIO()
    writer = csv.writer(bio)
    writer.writerow(headers)
    for row in data_array:
        writer.writerow(row)

    bio.seek(0)
    return bio


class SearchParserOld:

    def parse_condition(self, d):
        from polylogyx.search_rules import OPERATOR_MAP

        op = d['operator']
        value = d['value']

        # If this is a "column operator" - i.e. operating on a particular
        # value in a column - then we need to give a custom extraction
        # function that knows how to get this value from a query.
        column_name = None
        if d['field'] == 'column':
            # Strip 'column_' prefix to get the 'real' operator.
            if op.startswith('column_'):
                op = op[7:]
            if isinstance(value, six.string_types):
                column_name = value
            else:
                # The 'value' array will look like ['column_name', 'actual value']
                column_name, value = value
        if not column_name:
            column_name = d['field']
        klass = OPERATOR_MAP.get(op)

        if not klass:
            raise ValueError("Unsupported operator: {0}".format(op))

        inst = self.make_condition(klass, d['field'], value, column_name=column_name)
        return inst

    def parse_group(self, d):
        from polylogyx.search_rules import AndCondition, OrCondition

        if len(d['rules']) == 0:
            raise ValueError("A group contains no rules")
        upstreams = [self.parse(r) for r in d['rules']]
        condition = d['condition']
        if condition == 'AND' or condition == 'and':
            return self.make_condition(AndCondition, upstreams)
        elif condition == 'OR' or condition == 'or':
            return self.make_condition(OrCondition, upstreams)

        raise ValueError("Unknown condition: {0}".format(condition))

    def parse(self, d):
        if 'condition' in d:
            return self.parse_group(d)
        return self.parse_condition(d)

    def make_condition(self, klass, *args, **kwargs):
        from polylogyx.search_rules import BaseCondition

        """
        Memoizing constructor for conditions.  Uses the input config as the cache key.
        """
        conditions = {}

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


def valid_string_parser(string):
    pattern = '^[A-Za-z0-9_@.-]+$'
    if re.match(pattern, string):
        return True
    else:
        return False


def validate_file_size(f):
    """
       Decorator to make sure the  uploaded file size within configured size
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            blob = request.files['file'].read()
            size = len(blob)
            request.files['file'].seek(0)
        except Exception as e:
            size = 0
        if size > (1024 * 1024 * int(current_app.config.get('INI_CONFIG', {}).get('content_max_length'))):
            return abort(413, {'message': 'Request entity is too large ,please upload file size below {0} MB'.format(current_app.config.get('INI_CONFIG', {}).get('content_max_length'))})
        else:
            return f(*args, **kwargs)

    return decorated_function


def is_email_valid(email_input):
    import re
    pattern = r"^\S+@\S+\.\S+$"
    if email_input is None or (isinstance(email_input, str) and re.match(pattern, email_input)):
        return email_input
    raise ValueError('Provided email is not in a valid format!')
