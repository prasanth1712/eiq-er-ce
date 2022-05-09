from flask_restplus import Namespace, Resource
from flask import abort

from polylogyx.blueprints.v1.utils import *

from polylogyx.dao.v1 import alerts_dao, hosts_dao
from polylogyx.wrappers.v1 import parent_wrappers,alert_wrappers
from polylogyx.extensions import get_current_user
from polylogyx.authorize import authorize, is_current_user_an_admin, MyUnauthorizedException

ns = Namespace('alerts', description='Alerts related operations')


@ns.route('/count_by_source', endpoint='alert source count')
class AlertSourceCount(Resource):
    from flask_restplus import inputs

    parser = requestparse(['resolved', 'duration', 'type', 'date', 'host_identifier', 'rule_id'],
                          [inputs.boolean, int, int, str, str, int],
                          ['True to get all resolved alerts', 'duration', 'type', 'date', 'host_identifier', 'rule id'],
                          [False, False, False, False, False, False],
                          [None, [1, 2, 3, 4], [1, 2], None, None, None],
                          [None, 3, 2, None, None, None])

    @ns.expect(parser)
    @ns.marshal_with(parent_wrappers.common_response_wrapper)
    def get(self):
        args = self.parser.parse_args()
        start_date = None
        end_date = None
        if args['date']:
            try:
                start_date, end_date = get_start_dat_end_date(args)
            except Exception as e:
                current_app.logger.error('Date format passed is invalid! - {}'.format(str(e)))
                return abort(400, {'message': 'Date format passed is invalid!'})
        node = hosts_dao.get_node_by_host_identifier(args['host_identifier'])
        alert_source_tuple_list = alerts_dao.get_distinct_alert_source(args['resolved'], start_date, end_date, node,
                                                                       args['rule_id'])
        source_names = ['virustotal', 'rule', 'ibmxforce', 'alienvault', 'ioc']
        alert_source_count = [{'name': source, 'count': 0} for source in source_names]
        for source in alert_source_count:
            for source_count in alert_source_tuple_list:
                if source['name'] == source_count[0]:
                    source['count'] = source_count[1]
        alerts_data = {"alert_source": alert_source_count}
        if alerts_data['alert_source']:
            message = 'Data is fetched successfully'
            status = 'success'
        else:
            message = 'No data present'
            status = 'failure'
            alerts_data = {}
        return marshal(prepare_response(message, status, alerts_data),
                       parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('', endpoint='alert data')
class AlertsData(Resource):
    from flask_restplus import inputs

    parser = requestparse(['start', 'limit', 'source', 'searchterm', 'resolved', 'event_ids', 'duration', 'type',
                           'date', 'host_identifier', 'query_name', 'rule_id', 'events_count'],
                          [int, int, str, str, inputs.boolean, list, int, int, str, str, str, int, inputs.boolean],
                          ['Start', 'Limit', 'source', 'searchterm',
                           'True to get all resolved alerts', 'Event Ids', 'Duration', 'Type', 'Date',
                           'host_identifier', 'query_name', 'rule_id', 'events_count(true/false)'],
                          [False, False, False, False, False, False, False, False, False, False, False, False, False],
                          [None, None, None, None, None, None, [1, 2, 3, 4], [1, 2], None, None, None, None, None],
                          [0, 10, None, "", False, None, 3, 2, None, None, None, None, True])

    put_parser = requestparse(['resolve', 'alert_ids','verdict','comment'], [inputs.boolean, list,inputs.boolean,str],
                              ['Set True to resolve or False to move to non-resolved state',
                               'alert ids to resolve/unresolve','alert is true postive or false positive','comment'],
                              [False, True, False, False])

    @ns.expect(parser)
    def post(self):
        """ Display Alerts by source table content. """
        from polylogyx.dao.v1.hosts_dao import get_node_by_host_identifier
        from polylogyx.dao.v1.queries_dao import get_query_by_name
        from polylogyx.dao.v1.rules_dao import get_rule_by_id
        args = self.parser.parse_args()
        source = args['source']
        start = args['start']
        limit = args['limit']
        resolved = args['resolved']
        event_ids = args['event_ids']
        query_name = args['query_name']
        rule_id = args['rule_id']
        start_date = None
        end_date = None
        node_id = None

        if args['host_identifier']:
            node = get_node_by_host_identifier(args['host_identifier'])
            if not node:
                return marshal(prepare_response("No Host present for the host identifier given!", "failure"),
                               parent_wrappers.common_response_wrapper, skip_none=True)
            node_id = node.id
        if query_name and not get_query_by_name(query_name):
            return marshal(prepare_response("No Query present for the query name given!", "failure"),
                           parent_wrappers.common_response_wrapper, skip_none=True)
        if rule_id and not get_rule_by_id(rule_id):
            return marshal(prepare_response("No Rule present for the rule id given!", "failure"),
                           parent_wrappers.common_response_wrapper, skip_none=True)
        if args['date']:
            try:
                start_date, end_date = get_start_dat_end_date(args)
            except Exception as e:
                current_app.logger.error('Date format passed is invalid! - {}'.format(str(e)))
                return abort(400, {'message': 'Date format passed is invalid!'})

        results = get_results_by_alert_source(start, limit, source, args['searchterm'], resolved, event_ids, start_date,
                                              end_date, node_id, query_name, rule_id, args['events_count'])
        message = "Data is fetched successfully"
        status = "success"
        return marshal(prepare_response(message, status, results), parent_wrappers.common_response_wrapper, skip_none=True)

    @ns.expect(put_parser)
    def put(self):
        args = self.put_parser.parse_args()
        status = args['resolve']
        if status is False:
            if not is_current_user_an_admin():
                raise MyUnauthorizedException
        alert_ids = args['alert_ids']
        if status :
            if args['verdict'] is None:
                return abort(400, {'message': 'please provide user verdict is alert true positive or false postive'})
            alerts_dao.edit_alerts_status_by_alert(alert_ids, True, args['verdict'], args['comment'])
            current_app.logger.warning("Alerts with ids {} are resolved".format(alert_ids))
        else:
            alerts_dao.edit_alerts_status_by_alert(alert_ids)
            current_app.logger.warning("Alerts with ids {} are moved to OPEN state from resolved".format(alert_ids))
        message = "Selected alerts status is changed successfully"
        status = "success"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/<int:alert_id>', endpoint='alert investigate')
class AlertInvestigate(Resource):

    @ns.marshal_with(parent_wrappers.common_response_wrapper)
    def get(self, alert_id):
        alert = alerts_dao.get_alerts_by_alert_id(alert_id)
        if alert:
            alert = alerts_details(alert)
            message = "Successfully fetched the Alerts data"
            status = 'success'
        else:
            message = 'No Alerts present for the alert id given'
            status = 'failure'
            alert = {}
        return marshal(prepare_response(message, status, alert),
                       parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/<int:alert_id>/alerted_events', endpoint='alerted events')
class AlertAggregatedEvents(Resource):
    parser = requestparse(['query_name', 'start', 'limit', 'searchterm', 'column_name', 'column_value'],
                          [str, int, int, str, str, str],
                          ["query", "start count", "end count", "searchterm", "column_name", "column_value"],
                          [False, False, False, False, False, False], [None, None, None, None, None, None],
                          [None, 0, 10, "", None, None])

    @ns.expect(parser)
    def post(self, alert_id):
        args = self.parser.parse_args()
        data = None
        if args['column_value']:
            column_values = tuple([x.strip() for x in str(args['column_value']).split(',')])
        else:
            column_values = None
        alert = alerts_dao.get_alerts_by_alert_id(alert_id)
        if alert:
            if args['query_name']:
                queryset = alerts_dao.get_all_events_of_an_alert(alert, args['query_name'], args['start'], args['limit'],
                                                          args['searchterm'], args['column_name'], column_values)
                events = [{"id": event.id, "columns": event.columns, "action": event.action,
                           "timestamp": str(event.timestamp)} for event in queryset[2]]
                data = {"total_count": queryset[0], "count": queryset[1], "results": events}
            else:
                data = alerts_dao.get_alerted_queries(alert)
            message = "Successfully fetched the Alert's events data"
            status = 'success'
        else:
            message = 'No Alert present for the alert id given'
            status = 'failure'
        return marshal(prepare_response(message, status, data),
                       parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/<int:alert_id>/alerted_events/export', endpoint='alerted events export')
class AlertAggregatedEventsExport(Resource):
    parser = requestparse(['query_name', 'searchterm', 'column_name', 'column_value'],
                          [str, str, str, str],
                          ["query", "searchterm", "column_name", "column_value"],
                          [True, False, False, False], [None, None, None, None], [None, "", None, None])

    @ns.expect(parser)
    def get(self, alert_id):
        args = self.parser.parse_args()
        alert = alerts_dao.get_alerts_by_alert_id(alert_id)
        if args['column_value']:
            column_values = tuple([x.strip() for x in str(args['column_value']).split(',')])
        else:
            column_values = None
        if alert:
            queryset = alerts_dao.get_alerted_events_to_export(alert, args['query_name'], args['searchterm'],
                                                        args['column_name'], column_values)
            if queryset:
                bio = result_log_columns_export_using_query_set(queryset)
                response = send_file(
                    bio,
                    mimetype='text/csv',
                    as_attachment=True,
                    attachment_filename=args['query_name'] + '_alert' + str(alert_id) + str(dt.datetime.now()) + '.csv'
                )
                return response
            else:
                message = 'No similar alerting events'
                status = 'failure'
        else:
            message = 'No Alert present for the alert id given'
            status = 'failure'
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/alert_source/export', endpoint='export alert')
class ExportCsvAlerts(Resource):
    parser = requestparse(['source', 'duration', 'type', 'date', 'host_identifier', 'rule_id', 'event_ids'],
                          [str, int, int, str, str, int, list],
                          ['source name', 'duration', 'type', 'date', 'host identifier', 'rule id', 'event_ids'],
                          [True, False, False, False, False, False, False],
                          [None, [1, 2, 3, 4], [1, 2], None, None, None, None],
                          [None, 3, 2, None, None, None, None])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        source = args['source']
        start_date = None
        end_date = None
        if args['date']:
            try:
                start_date, end_date = get_start_dat_end_date(args)
            except Exception as e:
                current_app.logger.error('Date format passed is invalid! - {}'.format(str(e)))
                return abort(400, {'message': 'Date format passed is invalid!'})
        node = hosts_dao.get_node_by_host_identifier(args['host_identifier'])
        results = alerts_dao.get_alert_source(source, start_date, end_date, node, args['rule_id'], args['event_ids'])
        return get_response([alert.to_dict() for alert in results])
