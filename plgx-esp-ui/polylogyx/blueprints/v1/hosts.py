from flask_restful import Resource, inputs
from polylogyx.blueprints.v1.utils import *
from polylogyx.blueprints.v1.external_api import api
from polylogyx.utils import assemble_configuration, assemble_additional_configuration
from polylogyx.dao.v1 import hosts_dao, tags_dao, common_dao
from polylogyx.wrappers.v1 import host_wrappers, parent_wrappers, config_wrappers
from polylogyx.tasks import celery
from polylogyx.authorize import admin_required
from polylogyx.cache import refresh_cached_hosts, add_or_update_cached_host, merge_dicts, get_a_host
from polylogyx.db.signals import bulk_insert_to_pa
from sqlalchemy import desc, and_, or_

keys_to_update = ['last_ip', 'enrolled_on', 'last_checkin', 'last_status', 'last_result', 'last_config',
                  'last_query_read', 'last_query_write', 'host_details']


@api.resource('/hosts')
class HostsList(Resource):
    """
        List all Nodes Filters
    """
    parser = requestparse(['status', 'platform', 'searchterm', 'start', 'limit', 'enabled', 'alerts_count', 'column', 'order_by'],
                          [bool, str, str, int, int, inputs.boolean, inputs.boolean, str, str],
                          ['status(true/false)', 'platform(windows/linux/darwin)', 'searchterm', 'start', 'limit',
                           'enabled(true/false)', 'alerts_count(true/false)', 'column to order', 'orderby(asc/desc)'],
                          [False, False, False, False, False, False, False, False, False],
                          [None, ["windows", "linux", "darwin"], None, None, None, None, None, ['host', 'state', 'health', 'os', 'last_ip'], ['ASC', 'asc', 'Asc', 'DESC', 'desc', 'Desc']],
                          [None, None, "", None, None, None, True, None, None])

    def post(self):
        args = self.parser.parse_args()
        query_set = hosts_dao.get_hosts_paginated(args['status'], args['platform'], args['searchterm'], args['enabled'],
                                                  args['alerts_count'], args['column'], args['order_by']).offset(
            args['start']).limit(args['limit']).all()
        total_count = hosts_dao.get_hosts_total_count(args['status'], args['platform'], args['enabled'])
        if query_set:
            results = []
            for node_alert_count_pair in query_set:
                if args['alerts_count']:
                    node_dict = node_alert_count_pair[0].get_dict()
                    node_dict['alerts_count'] = node_alert_count_pair[1]
                    cached_host = get_a_host(node_key=node_alert_count_pair[0].node_key)
                else:
                    node_dict = node_alert_count_pair.get_node_dict()
                    cached_host = get_a_host(node_key=node_alert_count_pair.node_key)
                node_dict = merge_dicts(node_dict, {key: cached_host[key] for key in cached_host if key in keys_to_update})
                results.append(node_dict)
            data = {'results': results, 'count': hosts_dao.get_hosts_paginated(args['status'], args['platform'],
                                                                               args['searchterm'], args['enabled'],
                                                                               args['alerts_count']).count(),
                    'total_count': total_count}
        else:
            data = {'results': [], 'count': 0, 'total_count': total_count}
        status = "success"
        message = "Successfully fetched the hosts details"
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/export')
class NodesCSV(Resource):
    """
        Returns a csv file object with nodes info as data
    """

    parser = requestparse(
        ['status', 'platform', 'searchterm', 'start', 'limit', 'enabled', 'alerts_count', 'column', 'order_by'],
        [bool, str, str, int, int, inputs.boolean, inputs.boolean, str, str],
        ['status(true/false)', 'platform(windows/linux/darwin)', 'searchterm', 'start', 'limit',
         'enabled(true/false)', 'alerts_count(true/false)', 'column to order', 'orderby(asc/desc)'],
        [False, False, False, False, False, False, False, False, False],
        [None, ["windows", "linux", "darwin"], None, None, None, None, None,
         ['host', 'state', 'health', 'os', 'last_ip'], ['ASC', 'asc', 'Asc', 'DESC', 'desc', 'Desc']],
        [None, None, "", None, None, None, True, None, None])

    def get(self):
        from polylogyx.constants import ModelStatusFilters
        record_query = db.session.query(Node, db.func.count(Alerts.id))\
            .filter(ModelStatusFilters.HOSTS_NON_DELETED)\
            .outerjoin(Alerts, and_(Alerts.node_id == Node.id,
                                    ModelStatusFilters.ALERTS_NON_RESOLVED))\
            .group_by(Node.id).order_by(desc(Node.id)).all()
        results = []
        for node, alerts_count in record_query:
            res = {}
            res['id'] = node.id
            res['hostname'] = node.display_name
            res['host identifier'] = node.host_identifier
            if node.node_is_active():
                res['state'] = "online"
            else:
                res['state'] = "offline"
            if alerts_count:
                res['health'] = 'Unsafe'
            else:
                res['health'] = 'Safe'
            res['alerts count'] = alerts_count
            if node.os_info:
                res['operating system'] = node.os_info['name']
            else:
                res['operating system'] = node.platform
            res['last ip'] = node.last_ip
            res['tags'] = [tag.to_dict() for tag in node.tags]
            res['platform'] = node.platform
            results.append(res)

        headers = []
        if results:
            first_record = results[0]
            for key in first_record.keys():
                headers.append(key)
        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerow(headers)

        for data in results:
            row = []
            row.extend([data.get(column, '') for column in headers])
            writer.writerow(row)

        bio.seek(0)

        file_data = send_file(
            bio,
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename='nodes.csv'
        )
        return file_data

    def post(self):
        args = self.parser.parse_args()
        query_set = hosts_dao.get_hosts_paginated(args['status'], args['platform'], args['searchterm'], args['enabled'],
                                           args['alerts_count'],args['column'],args['order_by']).offset(args['start']).limit(args['limit']).all()
        if query_set:
            data = []
            for node_alert_count_pair in query_set:
                if args['alerts_count']:
                   node_dict = node_alert_count_pair[0].get_dict()
                   node_dict['alerts_count'] = node_alert_count_pair[1]
                else:
                   node_dict = node_alert_count_pair.get_node_dict()
                data.append(node_dict)
        else:
            data= []
        results = []
        for node in data:
            res={}
            res['id'] = node['id']
            res['hostname'] = node['display_name']
            res['host identifier'] =node['host_identifier']
            res['last ip']= node['last_ip']
            res['tags'] = node ['tags']
            if node['alerts_count']:
                res['health'] = 'Unsafe'
            else:
                res['health'] = 'Safe'
            if node['is_active']:
                res['state'] = "online"
            else:
                res['state'] = "offline"
            if 'os_info' in node:
                res['operating system'] = node['os_info']['name']
            else:
                res['operating system'] = node['platform']
            res['alerts count'] = node['alerts_count']
            results.append(res)

        headers = []
        if results:
            first_record = results[0]
            for key in first_record.keys():
                headers.append(key)
        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerow(headers)

        for data in results:
            row = []
            row.extend([data.get(column, '') for column in headers])
            writer.writerow(row)

        bio.seek(0)

        file_data = send_file(
           bio,
           mimetype='text/csv',
           as_attachment=True,
           attachment_filename='hosts.csv'
        )
        return file_data


@api.resource('/hosts/<string:host_identifier>', '/hosts/<int:node_id>')
class NodeDetailsList(Resource):
    """
        List a Node Details
    """
    def get(self, host_identifier=None, node_id=None):
        data = None
        if node_id:
            queryset = hosts_dao.get_node_by_id(node_id)
        elif host_identifier:
            queryset = hosts_dao.get_node_by_host_identifier(host_identifier)
        else:
            queryset = None

        if not queryset:
            message = "There is no host exists with this host identifier or node id given!"
            status = "failure"
        else:
            data = marshal(queryset, host_wrappers.nodewrapper)
            host_dict = get_a_host(node_key=data['node_key'])
            if host_dict:
                data = merge_dicts(data, {key: host_dict[key] for key in host_dict if key in keys_to_update})
            if not data:
                data = {}
            message = "Node details are fetched successfully"
            status = "success"
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/<string:host_identifier>/alerts/distribution', '/hosts/<int:node_id>/alerts/distribution',endpoint='host_alerts_count_for_host_identifier')
class HostAlertsDistribution(Resource):
    """
        List a Node Details
    """

    def get(self, host_identifier=None, node_id=None):
        if node_id:
            node = hosts_dao.get_node_by_id(node_id)
        elif host_identifier:
            node = hosts_dao.get_node_by_host_identifier(host_identifier)
        else:
            node = None
        if not node:
            data = None
            message = "There is no host exists with this host identifier or node id given!"
            status = "failure"
        else:
            data = {}
            data['sources'] = hosts_dao.host_alerts_distribution_by_source(node)
            data['rules'] = [{"name": rule_count_pair[0], "count": rule_count_pair[1]}
                             for rule_count_pair in hosts_dao.host_alerts_distribution_by_rule(node)]
            message = "Alerts distribution details are fetched for the host"
            status = "success"
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/count', endpoint='nodes_related_count')
class NodeCountList(Resource):
    """
        Lists all Nodes Filtered count
    """

    def get(self):
        data = hosts_dao.get_hosts_filtered_status_platform_count()
        return marshal(prepare_response("Successfully fetched the nodes status count", 'success', data),
                       parent_wrappers.common_response_wrapper)


@api.resource('/hosts/status_logs', endpoint='node_status_logs')
class HostStatusLogs(Resource):
    """
        Host Status Logs
    """
    parser = requestparse(['host_identifier', 'node_id', 'start', 'limit', 'searchterm'], [str, int, int, int, str],
                          ["host identifier of the node", "id of the node", 'start', 'limit', 'searchterm'],
                          [False, False, False, False, False], [None, None, None, None, None],
                          [None, None, None, None, ''])

    def post(self):
        args = self.parser.parse_args()
        data = None
        status = "failure"
        if args['node_id'] is not None or args['host_identifier'] is not None:
            if args['host_identifier'] is not None:
                qs = hosts_dao.get_node_by_host_identifier(args['host_identifier'])
            else:
                node_id = args['node_id']
                qs = hosts_dao.get_node_by_id(node_id)
            if qs:
                data = {'results': marshal(hosts_dao.get_status_logs_of_a_node(qs, args['searchterm'])
                                           .offset(args['start']).limit(args['limit']).all(),
                                           host_wrappers.node_status_log_wrapper),
                        'count': hosts_dao.get_status_logs_of_a_node(qs, args['searchterm']).count(),
                        'total_count': hosts_dao.get_status_logs_total_count(qs)}
                message = "Successfully fetched the host's status logs"
                status = "success"
            else:
                message = "Host identifier or node id passed is not correct!"
        else:
            message = "Please pass one of node id or host identifier!"

        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/additional_config', endpoint='node_additional_config')
class HostAdditionalConfig(Resource):
    """
        Additional Config of a Node
    """
    parser = requestparse(['host_identifier', 'node_id'], [str, int], ["host identifier of the node", "id of the node"],
                          [False, False])

    def post(self):
        args = self.parser.parse_args()
        config = None
        status = "failure"
        if args['node_id'] is not None or args['host_identifier'] is not None:
            if args['host_identifier'] is not None:
                node = hosts_dao.get_node_by_host_identifier(args['host_identifier'])
            else:
                node_id = args['node_id']
                node = hosts_dao.get_node_by_id(node_id)
            if node:
                config = assemble_additional_configuration(node)
                current_app.logger.debug("Additional config of Node '{0}' is:\n{1}".format(node, config))
                status = "success"
                message = "Successfully fetched additional config of the node for the host identifier passed"
            else:
                message = "Host identifier or node id passed is not correct!"
        else:
            message = "At least one of host identifier or node id should be given!"

        return marshal(prepare_response(message, status, config), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/config', endpoint='node_full_config')
class HostFullConfig(Resource):
    """
        Full Config of a Node
    """
    parser = requestparse(['host_identifier', 'node_id'], [str, int], ["host identifier of the node", "id of the node"],
                          [False, False])

    def post(self):
        args = self.parser.parse_args()
        config = None
        config_details = None
        status = "failure"
        if args['node_id'] is not None or args['host_identifier'] is not None:
            if args['host_identifier'] is not None:
                node = hosts_dao.get_node_by_host_identifier(args['host_identifier'])
            else:
                node_id = args['node_id']
                node = hosts_dao.get_node_by_id(node_id)
            if node:
                config = assemble_configuration(node)
                config_details = config[1]
                config = config[0]
                current_app.logger.debug("Full config of Node '{0}' is:\n{1}".format(node, config_details))
                status = "success"
                message = "Successfully fetched full config of the node for the host identifier passed"
            else:
                message = "Host identifier or node id passed is not correct!"
        else:
            message = "At least one of host identifier or node id should be given!"
        return marshal({'status': status, 'message': message, 'data': config, 'config': config_details}, 
                       config_wrappers.node_config)


@api.resource('/hosts/recent_activity/count', endpoint='node_recent_activity_count')
class RecentActivityCount(Resource):
    """
        Recent Activity count of a Node
    """
    parser = requestparse(['host_identifier', 'node_id'], [str, int],
                          ["host identifier of the node", "id of the node"], [False, False])

    def post(self):
        args = self.parser.parse_args()
        status = "failure"
        data = None
        if args['node_id'] is not None or args['host_identifier'] is not None:
            if args['host_identifier'] is not None:
                node = hosts_dao.get_node_by_host_identifier(args['host_identifier'])
                if node:
                    node_id = node.id
                else:
                    node_id = None
            else:
                node_id = args['node_id']
            if not node_id:
                message = "Please pass correct host identifier or node id to get the results"
            else:
                data = [{'name': query[0], 'count': query[1]} for query in hosts_dao.get_result_log_count(node_id)]
                status = "success"
                message = "Successfully fetched the count of schedule query results count of host identifier passed"
        else:
            message = "At least one of host identifier or node id should be given!"
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/recent_activity', endpoint='node_recent_activity_results')
class RecentActivityResults(Resource):
    """
        Recent Activity results of a query of a Node
    """

    parser = requestparse(['host_identifier', 'node_id', 'query_name', 'start', 'limit', 'searchterm',
                           'column_name', 'column_value'], [str, int, str, int, int, str, str, str],
                          ["host identifier of the node", "node_id", "query", "start id", "limit",
                           "searchterm", "column_name", "column_value"],
                          [False, False, True, False, False, False, False, False],
                          [None, None, None, None, None, None, None, None],
                          [None, None, None, 0, 10, "", None, None])

    def post(self):
        args = self.parser.parse_args()
        status = "failure"
        data = {}
        if args['column_value']:
            column_values = tuple([x.strip() for x in str(args['column_value']).split(',') if x])
        else:
            column_values = None
        if args['node_id'] is not None or args['host_identifier'] is not None:
            if args['host_identifier'] is not None:
                node = hosts_dao.get_node_by_host_identifier(args['host_identifier'])
                if node:
                    node_id = node.id
                else:
                    node_id = None
            else:
                node_id = args['node_id']
            if not node_id:
                message = "Please pass correct host identifier or node id to get the results"
            else:
                try:
                    qs = hosts_dao.get_result_log_of_a_query_opt(node_id, args['query_name'], args['start'],
                                                       args['limit'], args['searchterm'], args['column_name'],
                                                       column_values)
                    data = {'count': qs[0], 'total_count': qs[2], 'categorized_count': qs[3], 'results': [
                        {'id': list_ele[0], 'timestamp': list_ele[1].strftime('%m/%d/%Y %H/%M/%S'), 'action': list_ele[2],
                         'columns': list_ele[3]} for list_ele in qs[1]]}
                    status = "success"
                    message = "Successfully fetched the count of schedule query results count of host identifier passed"
                except Exception as e:
                    message = "Unable to fetch scheduled query results for the node '<Node {0}>' " \
                            "and the query '{1}' - {2}".format(node_id, args['query_name'], str(e))
                    current_app.logger.error(message)
                    db.session.commit()
        else:
            message = "At least one of host identifier or node id should be given!"

        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


# Modify Tag section

@api.resource('/hosts/<string:host_identifier>/tags', endpoint='node_tags')
@api.resource('/hosts/<int:node_id>/tags', endpoint='node_tags_by_node_id')
class ListTagsOfNode(Resource):
    """
        Resource for tags of a host
    """
    parser = requestparse(['tag'], [str],
                          ["tag to add/remove for the node"], [True])

    def get(self, host_identifier=None, node_id=None):
        """
            Lists tags of a node by its host_identifier
        """
        status = 'failure'
        if host_identifier:
            node = hosts_dao.get_node_by_host_identifier(host_identifier)
        elif node_id:
            node = hosts_dao.get_node_by_id(node_id)
        else:
            node = None
        if not node:
            message = "Host id or node id passed it not correct"
            data = None
        else:
            data = [tag.value for tag in node.tags]
            status = "success"
            message = "Successfully fetched the tags of host"
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)

    @admin_required
    def post(self, host_identifier=None, node_id=None):
        """
            Creates tags of a node by its host_identifier
        """
        args = self.parser.parse_args()
        status = 'failure'

        if host_identifier:
            node = hosts_dao.get_node_by_host_identifier(host_identifier)
        elif node_id:
            node = hosts_dao.get_node_by_id(node_id)
        else:
            node = None
        if node:
            tag = args['tag'].strip()
            if not tag or not valid_string_parser(tag):
                message = "Tag provided is not valid"
            elif not (0 < len(tag) < int(current_app.config.get('INI_CONFIG', {}).get('max_tag_length'))):
                message = f"Tag length should be between 0 and {current_app.config.get('INI_CONFIG', {}).get('max_tag_length')}"
            else:
                tag = tags_dao.create_tag_obj(tag)
                node.tags.append(tag)
                node.save()
                status = "success"
                message = "Successfully created tags to host"
                current_app.logger.info("Successfully created tag '{0}' to host '{1}'".format(tag, node))
        else:
            message = "Host id or node id passed it not correct"

        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)

    @admin_required
    def delete(self, host_identifier=None, node_id=None):
        """
            Remove tags of a node by its host_identifier
        """
        args = self.parser.parse_args()
        status = 'failure'

        if host_identifier:
            node = hosts_dao.get_node_by_host_identifier(host_identifier)
        elif node_id:
            node = hosts_dao.get_node_by_id(node_id)
        else:
            node = None
        if node:
            tag = args['tag'].strip()
            tag = tags_dao.get_tag_by_value(tag)
            if tag:
                if hosts_dao.is_tag_of_node(node, tag):
                    node.tags.remove(tag)
                    node.save()
                    message = "Successfully removed tags from host"
                    status = "success"
                    current_app.logger.info("Successfully removed tag '{0}' from the host '{1}'".format(tag, node))
                else:
                    message = "Tag provided is not in host's tag list, Please check tag once again"
            else:
                message = "Tag provided does not exists"
        else:
            message = "Host id or node id passed it not correct"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/search/export', endpoint="nodes_search_export")
class ExportNodeSearchQueryCSV(Resource):
    """
        Export node search query to csv
    """
    parser = requestparse(['conditions', 'host_identifier', 'query_name', 'node_id', 'column_name', 'column_value'],
                          [dict, str, str, int, str, str],
                          ["conditions to search for", 'host_identifier of the node', 'name of the schedule query',
                           'id of the node', 'column_name', 'column_value'],
                          [False, False, True, False, False, False])

    def post(self):
        args = self.parser.parse_args()
        host_identifier = args['host_identifier']
        conditions = args['conditions']
        query_name = args['query_name']
        node_id = args['node_id']
        if args['column_value']:
            column_values = list([x.strip() for x in str(args['column_value']).split(',')])
        else:
            column_values = None

        if node_id or host_identifier:
            if host_identifier:
                node_id = get_node_id_by_host_id(host_identifier)
                if not node_id:
                    return marshal(prepare_response("Host identifier given is invalid!", "failure"),
                                   parent_wrappers.common_response_wrapper)
        else:
            return marshal(prepare_response("At least one of host identifier or node id is required!", "failure"), 
                           parent_wrappers.common_response_wrapper)
        if conditions:
            try:
                search_rules = SearchParser()
                root = search_rules.parse_group(conditions)
                filter = root.run('', [], 'result_log')
            except Exception as e:
                message = str(e)
                return marshal(prepare_response(message, "failure"), parent_wrappers.common_response_wrapper)
        else:
            filter = None
        try:
            results = hosts_dao.node_result_log_search_results(filter, node_id, query_name, args['column_name'], column_values)
        except Exception as e:
            message = "Unable to find data for the payload given - {}".format(str(e))
            return marshal(prepare_response(message, "failure"), parent_wrappers.common_response_wrapper)

        if results:
            results = [r for r, in results]
            bio = result_log_columns_export_using_query_set(results)
            response = send_file(
                bio,
                mimetype='text/csv',
                as_attachment=True,
                attachment_filename=query_name+'_'+str(node_id)+str(dt.datetime.now())+'.csv'
            )
            return response
        else:
            message = "There are no matching results for the payload given"
        return marshal(prepare_response(message, "failure"), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/<string:host_identifier>/delete', endpoint='node_removed')
@api.resource('/hosts/<int:node_id>/delete', endpoint='node_removed_by_id')
class NodeRemove(Resource):
    """
        Disable node
    """

    @admin_required
    def delete(self, host_identifier=None, node_id=None):
        node = None
        message = "Node is not present with this node id or host identifier"
        status = "failure"
        if host_identifier:
            node = hosts_dao.get_node_by_host_identifier(host_identifier)
        if node_id:
            node = hosts_dao.get_node_by_id(node_id)
        if node:
            current_app.logger.warning("Host {} is requested for permanent deletion".format(node.host_identifier))
            hosts_dao.delete_host(node)
            add_or_update_cached_host(node_obj=node)
            message = "Successfully deleted the host"
            status = "Success"
            return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)

    @admin_required
    def put(self, host_identifier=None, node_id=None):
        node = None
        message = "Node is not present with this node id or host identifier"
        status = "failure"
        if host_identifier:
            node = hosts_dao.get_node_by_host_identifier(host_identifier)
        if node_id:
            node = hosts_dao.get_node_by_id(node_id)
        if node:
            current_app.logger.warning("Host {} is requested to be disabled for all his activities from agent".format(host_identifier))
            hosts_dao.soft_remove_host(node)
            add_or_update_cached_host(node_obj=node)
            message = "Successfully removed the host"
            status = "Success"
            return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/<string:host_identifier>/enable', endpoint='node_enabled')
@api.resource('/hosts/<int:node_id>/enable', endpoint='node_enabled_by_id')
class NodeEnabled(Resource):
    """
        Enable back the node
    """

    @admin_required
    def put(self, host_identifier=None, node_id=None):
        node = None
        message = "Node is not present with this node id or host identifier"
        status = "failure"
        if host_identifier:
            node = hosts_dao.get_disable_node_by_host_identifier(host_identifier)
        if node_id:
            node = hosts_dao.get_disable_node_by_id(node_id)
        if node:
            current_app.logger.warning("Host {} is requested to be enabled again".format(node.host_identifier))
            hosts_dao.enable_host(node)
            add_or_update_cached_host(node_obj=node)
            message = "Successfully enabled the host"
            status = "Success"
            return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/status_log/export', endpoint='node_status_logs_export')
class HostStatusLogs(Resource):
    """
        Host Status Logs
    """
    parser = requestparse(['host_identifier', 'node_id',  'searchterm'], [str, int, str],
                          ["host identifier of the node", "id of the node",  'searchterm'],
                          [False, False, False], [None, None, ''], [None, None, ''])

    def post(self):
        from manage import declare_queue
        from celery import uuid
        task_id = uuid()
        args = self.parser.parse_args()
        status = "failure"
        if args['node_id'] is not None or args['host_identifier'] is not None:
            if args['host_identifier'] is not None:
                node = hosts_dao.get_node_by_host_identifier(args['host_identifier'])
                node_id = node.id
            else:
                node_id = args['node_id']

            task = fetch_data_from_db.apply_async(args=[node_id, task_id], task_id=task_id)
            status = 'Success'
            message = 'Downloading will be completed in sometime'
            current_app.logger.info("Started celery task to prepare csv exported file for status logs "
                                    "with task id '{0}' and node id is '{1}'".format(task_id, node_id))
            common_dao.create_csv_export_object('status_log', task.id, 'pending')
            declare_queue(task.id, type='csv_export')
        else:
            message = "Please pass one of node id or host identifier!"

        return marshal(prepare_response(message, status, {'task_id': task.id}), parent_wrappers.common_response_wrapper,)


@api.resource('/hosts/delete', endpoint='nodes_removed')
class NodeDelete(Resource):
    """
        Disable node
    """

    parser = requestparse(['host_identifiers', 'node_ids'], [str, str],
                          ["host identifier of the node", "id of the node"],
                          [False, False], [None, None], [None, None])


    @admin_required
    def delete(self):
        args = self.parser.parse_args()
        host_identifiers = args['host_identifiers']
        nodes = args['node_ids']
        if host_identifiers:
            host_identifiers = host_identifiers.split(',')
        if nodes:
            nodes = nodes.split(',')
        if not nodes and not host_identifiers:
            return marshal(prepare_response("At least one of host identifier or node id is required!", "failure"),
                           parent_wrappers.common_response_wrapper)
        hosts = hosts_dao.get_hosts(node_ids=nodes, host_identifiers=host_identifiers, state=Node.REMOVED)
        node_ids = [host.id for host in hosts]
        if not hosts:
            return marshal(prepare_response("Host identifier(s) or node id(s) provided is/are not valid for this activity!", "failure"),
                           parent_wrappers.common_response_wrapper)
        current_app.logger.warning("Hosts with node ids {} is/are requested for permanent deletion".format(node_ids))
        hosts_dao.delete_hosts(node_ids)
        bulk_insert_to_pa(db.session, 'deleted', Node, node_ids)
        db.session.commit()
        refresh_cached_hosts()
        message = "Successfully deleted the host"
        status = "Success"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)

    @admin_required
    def put(self):
        args = self.parser.parse_args()
        host_identifiers = args['host_identifiers']
        nodes = args['node_ids']
        if host_identifiers:
            host_identifiers = host_identifiers.split(',')
        if nodes:
            nodes = nodes.split(',')
        if not nodes and not host_identifiers:
            return marshal(prepare_response("At least one of host identifier or node id is required!", "failure"),
                           parent_wrappers.common_response_wrapper)
        hosts = hosts_dao.get_hosts(node_ids=nodes, host_identifiers=host_identifiers, state=Node.ACTIVE)
        node_ids = [host.id for host in hosts]
        if not hosts:
            return marshal(prepare_response("Host identifier(s) or node id(s) provided is/are not valid for this activity!", "failure"),
                           parent_wrappers.common_response_wrapper)
        current_app.logger.warning("Host {} is requested for removal".format(node_ids))
        hosts_dao.soft_remove_hosts(node_ids)
        bulk_insert_to_pa(db.session, 'updated', Node, node_ids)
        db.session.commit()
        refresh_cached_hosts()
        message = "Successfully removed the host"
        status = "Success"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/hosts/enable', endpoint='nodes_enabled')
class NodeEnable(Resource):
    """
        Disable node
    """

    parser = requestparse(['host_identifiers', 'node_ids'], [str, str],
                          ["host identifier of the node", "id of the node"],
                          [False, False], [None, None], [None, None])

    @admin_required
    def post(self):
        args = self.parser.parse_args()
        host_identifiers=args['host_identifiers']
        nodes= args['node_ids']
        if host_identifiers:
            host_identifiers=host_identifiers.split(',')
        if nodes:
            nodes=nodes.split(',')
        if not nodes and not host_identifiers:
            return marshal(prepare_response("At least one of host identifier or node id is required!", "failure"),
                           parent_wrappers.common_response_wrapper)
        hosts = hosts_dao.get_hosts(node_ids=nodes, host_identifiers=host_identifiers, state=Node.REMOVED)
        node_ids = [host.id for host in hosts]
        if not hosts:
            return marshal(prepare_response("Host identifier(s) or node id(s) provided is/are not valid for this activity!", "failure"),
                           parent_wrappers.common_response_wrapper)
        current_app.logger.warning("Host {} is requested for enabled again".format(node_ids))
        hosts_dao.enable_hosts(node_ids)
        bulk_insert_to_pa(db.session, 'enabled', Node, node_ids)
        db.session.commit()
        refresh_cached_hosts()
        message = "Successfully enabled the host"
        status = "Success"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@celery.task()
def fetch_data_from_db(node_id, task_id):
    from polylogyx.utils import form_status_log_csv, push_results_to_queue
    node = hosts_dao.get_node_by_id(node_id)
    try:
        results = hosts_dao.get_status_logs_of_a_node(node).all()
        results = marshal(results, host_wrappers.node_status_log_wrapper)
        status = 'success'
        data = form_status_log_csv(results, node_id)
        push_results_to_queue(data, task_id, 'csv_export_')
    except Exception as e:
        current_app.logger.error(str(e))
        status = 'failure'
    common_dao.update_csv_export_status(task_id, status)

