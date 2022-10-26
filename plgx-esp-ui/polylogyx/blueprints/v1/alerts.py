from flask_restful import Resource
from flask import abort
from polylogyx.blueprints.v1.utils import *
from polylogyx.blueprints.v1.external_api import  api
from polylogyx.dao.v1 import alerts_dao, hosts_dao
from polylogyx.wrappers.v1 import parent_wrappers,alert_wrappers
from polylogyx.extensions import get_current_user
from polylogyx.authorize import authorize, is_current_user_an_admin, MyUnauthorizedException


@api.resource('/alerts/count_by_source', endpoint='alert source count')
class AlertSourceCount(Resource):
    from flask_restful import inputs

    parser = requestparse(['resolved', 'duration', 'type', 'date', 'host_identifier', 'rule_id'],
                          [inputs.boolean, int, int, str, str, int],
                          ['True to get all resolved alerts', 'duration', 'type', 'date', 'host_identifier', 'rule id'],
                          [False, False, False, False, False, False],
                          [None, [1, 2, 3, 4], [1, 2], None, None, None],
                          [None, 3, 2, None, None, None])

    def get(self):
        args = self.parser.parse_args()
        start_date = None
        end_date = None
        if args['date']:
            try:
                start_date, end_date = get_start_date_end_date(args)
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
                       parent_wrappers.common_response_wrapper)


@api.resource('/alerts', endpoint='alert data')
class AlertsData(Resource):
    from flask_restful import inputs

    parser = requestparse(['start', 'limit', 'source', 'searchterm', 'resolved', 'event_ids', 'duration', 'type',
                           'date', 'host_identifier', 'query_name', 'rule_id', 'events_count','column','order_by','start_date','end_date','severity','verdict'],
                          [int, int, str, str, inputs.boolean, list, int, int, str, str, str, str, inputs.boolean,str,str,str,str,str,str],
                          ['Start', 'Limit', 'source', 'searchterm',
                           'True to get all resolved alerts', 'Event Ids', 'Duration', 'Type', 'Date',
                           'host_identifier', 'query_name', 'rule_id', 'events_count(true/false)','column','Order_by','start_date','end_date','severity','verdict'],
                          [False, False, False, False, False, False, False, False, False, False, False, False, False,False,False,False,False,False,False],
                          [None, None, None, None, None, None, [1, 2, 3, 4], [1, 2], None, None, None, None, None,[
                              'hostname','severity','rule','created_at','status'],['ASC','asc','Asc','DESC','desc','Desc'],None,None,None,None],
                          [0, 10, None, "", None, None, 3, 2, None, None, None, None, True,None,None,None,None,None,None])

    put_parser = requestparse(['resolve', 'alert_ids', 'verdict', 'comment'], [inputs.boolean, list,inputs.boolean,str],
                              ['Set True to resolve or False to move to non-resolved state',
                               'alert ids to resolve/unresolve','alert is true positive or false positive','comment'],
                              [False, True, False, False])
    
    def post(self):
        """ Display Alerts by source table content. """
        from polylogyx.dao.v1.hosts_dao import get_node_by_host_identifier
        from polylogyx.dao.v1.queries_dao import get_query_by_name
        from polylogyx.dao.v1.rules_dao import get_rule_by_id
        args = self.parser.parse_args()
        source = None
        start = args['start']
        limit = args['limit']
        resolved = args['resolved']
        event_ids = args['event_ids']
        query_name = args['query_name']
        rule_ids = None
        column = args['column']
        start_date = None
        end_date = None
        node_ids = None
        severity=None
        verdict=None
        if args['host_identifier']:
            nodes = args['host_identifier'].split(',')
            node_ids = [get_node_by_host_identifier(node).id for node in nodes if get_node_by_host_identifier(node)]
            if len(node_ids) == 0:
                return marshal(prepare_response("No Host present for the host identifier given!", "failure"),
                               parent_wrappers.common_response_wrapper)

        if query_name and not get_query_by_name(query_name):
            return marshal(prepare_response("No Query present for the query name given!", "failure"),
                           parent_wrappers.common_response_wrapper)
        if args['rule_id']:
            rule_ids = args['rule_id'].split(',')
            rule_ids = [rule_id for rule_id in rule_ids if get_rule_by_id(rule_id)]
            if len(rule_ids) == 0:
                return marshal(prepare_response("No Rule present for the rule id given!", "failure"),
                               parent_wrappers.common_response_wrapper)
        if args['source']:
            source = args['source'].split(',')
        if args['date'] or args['start_date']:
            try:
                start_date, end_date = get_start_date_end_date(args)
            except Exception as e:
                current_app.logger.error('Date format passed is invalid! - {}'.format(str(e)))
                return abort(400, {'message': 'Date format passed is invalid!'})
        if args['severity']:
            severity = args['severity'].split(',')
            severity = [sv if sv != 'warning' else 'medium' for sv in severity if sv in ['high', 'medium', 'low', 'critical','info','warning']]
            if len(severity) == 0:
                return abort(400,
                {'message': "please provide valid choice for severity ('low','info','medium','high','critical')"})
        if args['verdict']:
            verdict = args['verdict'].split(',')
            verdict = [vd for vd in verdict if vd in ['true_positive', 'false_positive', 'open']]
            if len(verdict) == 0:
                return abort(400, {
                    'message': "please provide valid choice for verdict ('true_positive','false_positive','open')"})

        results = get_results_by_alert_source(start, limit, source, args['searchterm'], resolved, event_ids, start_date,
                                              end_date, node_ids, query_name, rule_ids, args['events_count'],args['column'],args['order_by'],severity,verdict)
        message = "Data is fetched successfully"
        status = "success"
        return marshal(prepare_response(message, status, results), parent_wrappers.common_response_wrapper)

    def put(self):
        args = self.put_parser.parse_args()
        status = args['resolve']
        if status is False:
            if not is_current_user_an_admin():
                raise MyUnauthorizedException
        alert_ids = args['alert_ids']
        if status :
            if args['verdict'] is None:
                return abort(400, {'message': 'please provide user verdict either true positive or false postive'})
            alerts_dao.edit_alerts_status_by_alert(alert_ids, True, args['verdict'], args['comment'])
            current_app.logger.warning("Alerts with ids {} are resolved".format(alert_ids))
        else:
            alerts_dao.edit_alerts_status_by_alert(alert_ids)
            current_app.logger.warning("Alerts with ids {} are moved to OPEN state from resolved".format(alert_ids))
        message = "Selected alerts status is changed successfully"
        status = "success"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/alerts/<int:alert_id>', endpoint='alert investigate')
class AlertInvestigate(Resource):

    def get(self, alert_id):
        alert = alerts_dao.get_alerts_by_alert_id(alert_id)
        platform_activity = alerts_dao.get_platform_activity_by_alert_id(alert_id)
        if alert:
            alert = alerts_details(alert,platform_activity)
            message = "Successfully fetched the Alerts data"
            status = 'success'
        else:
            message = 'No Alerts present for the alert id given'
            status = 'failure'
            alert = {}
        return marshal(prepare_response(message, status, alert),
                       parent_wrappers.common_response_wrapper)


@api.resource('/alerts/<int:alert_id>/alerted_events', endpoint='alerted events')
class AlertAggregatedEvents(Resource):
    parser = requestparse(['query_name', 'start', 'limit', 'searchterm', 'column_name', 'column_value'],
                          [str, int, int, str, str, str],
                          ["query", "start count", "end count", "searchterm", "column_name", "column_value"],
                          [False, False, False, False, False, False], [None, None, None, None, None, None],
                          [None, 0, 10, "", None, None])

    
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
                       parent_wrappers.common_response_wrapper)


@api.resource('/alerts/<int:alert_id>/alerted_events/export', endpoint='alerted events export')
class AlertAggregatedEventsExport(Resource):
    parser = requestparse(['query_name', 'searchterm', 'column_name', 'column_value'],
                          [str, str, str, str],
                          ["query", "searchterm", "column_name", "column_value"],
                          [True, False, False, False], [None, None, None, None], [None, "", None, None])

    
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
                queryset = [r for r, in queryset]
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
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/alerts/alert_source/export', endpoint='export alert')
class ExportCsvAlerts(Resource):
    parser = requestparse(['source', 'duration', 'type', 'date', 'host_identifier', 'rule_id', 'event_ids',"start_date","end_date","severity","verdict","search"],
                          [str, int, int, str, str, str, list,str,str,str,str,str],
                          ['source name', 'duration', 'type', 'date', 'host identifier', 'rule id', 'event_ids','start_date','end_date','severity','verdict',"search"],
                          [False, False, False, False, False, False, False,False,False,False,False,False],
                          [None, [1, 2, 3, 4], [1, 2], None, None, None, None,None,None,None,None,None],
                          [None, 3, 2, None, None, None, None,None,None,None,None,None])

    
    def post(self):
        from polylogyx.dao.v1.hosts_dao import get_node_by_host_identifier
        from polylogyx.dao.v1.queries_dao import get_query_by_name
        from polylogyx.dao.v1.rules_dao import get_rule_by_id
        args = self.parser.parse_args()
        source = args['source']
        start_date = None
        end_date = None
        node_ids=None
        severity=None
        verdict=None
        rule_ids=None
        if args['source']:
            source=args['source'].split(',')
        if args['date'] or args['start_date']:
            try:
                start_date, end_date = get_start_date_end_date(args)
            except Exception as e:
                current_app.logger.error('Date format passed is invalid! - {}'.format(str(e)))
                return abort(400, {'message': 'Date format passed is invalid!'})
        if args['rule_id']:
            rule_ids=args['rule_id'].split(',')
            rule_ids = [ rule_id for rule_id in rule_ids if get_rule_by_id(rule_id)]
            if len(rule_ids)==0:
                return marshal(prepare_response("No Rule present for the rule id given!", "failure"),
                           parent_wrappers.common_response_wrapper)
        if args['severity']:
            severity = args['severity'].split(',')
            severity = [sv for sv in severity if sv in ['high', 'medium', 'low','info','critical']]
            if len(severity) == 0:
                return abort(400, {'message': "please provide valid choice for severity ('high','medium','low','info','critical')"})

        if args['verdict']:
            verdict = args['verdict'].split(',')
            verdict = [vd for vd in verdict if vd in ['true_positive', 'false_positive', 'open']]
            if len(verdict) == 0:
                return abort(400, {
                    'message': "please provide valid choice for verdict ('true_positive','false_positive','open')"})
        if args['host_identifier']:
            nodes=args['host_identifier'].split(',')
            node_ids=[get_node_by_host_identifier(node).id for node in nodes if get_node_by_host_identifier(node)]
            if len(node_ids)==0:
                return marshal(prepare_response("No Host present for the host identifier given!", "failure"),
                               parent_wrappers.common_response_wrapper)
        results = alerts_dao.get_alert_source(source, start_date, end_date, node_ids, rule_ids, args['event_ids'],severity,verdict,args['search'])
        return get_response([alert.to_dict() for alert in results])
