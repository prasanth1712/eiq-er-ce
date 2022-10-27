from flask_restful import  Resource
from flask import abort
from polylogyx.blueprints.v1.external_api import api
from polylogyx.dao.v1 import common_dao
from polylogyx.blueprints.v1.utils import *
from polylogyx.constants import PolyLogyxServerDefaults
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.authorize import admin_required

import json


@api.resource('/hunt-upload', endpoint="hunt_file_upload")
class HuntFileUpload(Resource):
    """
        Hunting through the file uploaded
    """

    from werkzeug import datastructures
    parser = requestparse(['file', 'type', 'host_identifier', "query_name", "start", "limit"],
                          [datastructures.FileStorage, str, str, str, int, int],
                          ['Threat file', 'type of hunt (md5/sha256/domain name)', 'host_identifier of the node',
                           "query_name", "start", "limit"],
                          [True, True, False, False, False, False],
                          [None, PolyLogyxServerDefaults.search_supporting_columns, None, None, None, None],
                          [None, None, None, None, 0, 100])

    @validate_file_size
    def post(self):
        args = self.parser.parse_args()
        data = None
        message = None
        status = "failure"
        lines = None

        indicator_type = args['type']
        file = args['file']
        query_name = args['query_name']
        host_identifier = args['host_identifier']
        start = args['start']
        limit = args['limit']

        try:
            lines = [line.decode('utf-8').replace('\n', '').replace('\r', '') for line in file.readlines() if line.decode('utf-8').replace('\n', '').replace('\r', '')]
        except Exception as e:
            message = "We are unable to read this file with this format!"
            current_app.logger.error("Unable to read file of this format - {0}".format(str(e)))
        if lines is not None:
            results = hunt_through_indicators(lines, indicator_type, host_identifier, query_name, start, limit)
        else:
            results = [message, status, data]
        return marshal(prepare_response(results[0], results[1], results[2]), parent_wrappers.common_response_wrapper)


def hunt_through_indicators(lines, indicator_type, host_identifier, query_name, start, limit):
    # method to hunt recent activity through indicators
    status = "failure"
    data = None
    if not host_identifier:
        output_list_data = []
        hunt_search_results = common_dao.result_log_query_count(lines, indicator_type)
        for search_result in hunt_search_results:
            data_dict = hosts_dao.get_host_id_and_name_by_node_id(search_result[0])
            query_count_pair = {"query_name": search_result[1], "count": search_result[2]}
            is_matched = False
            for host_result_log_item in output_list_data:
                if data_dict['host_identifier'] == host_result_log_item['host_identifier']:
                    is_matched = True
                    if 'queries' in host_result_log_item:
                        host_result_log_item['queries'].append(query_count_pair)
                    else:
                        host_result_log_item['queries'] = []
            if not is_matched:
                data_dict['queries'] = [query_count_pair]
                output_list_data.append(data_dict)

        message = "Successfully fetched the results through the hunt"
        status = "success"
        data = output_list_data
        if not output_list_data:
            data = []

    else:
        nodes = get_nodes_for_host_id(host_identifier)
        if not nodes:
            message = "Please provide correct host identifier!"
        elif not query_name:
            message = "Please provide the query name!"
        else:
            try:
                qs = common_dao.result_log_query(lines, indicator_type, [node.id for node in nodes], query_name, start,
                                                 limit)
                results = qs['results']
                results = [result[2] for result in results]
                count = qs['count']
                data = {'count': count, 'results': results}
                message = "Successfully fetched the results through the hunt"
                status = "success"
            except Exception as e:
                data = None
                message = str(e)
    return [message, status, data]


@api.resource('/indicators/hunt', endpoint="hunt_indicators")
class IndicatorHunt(Resource):
    """
        Hunting through the indicators given
    """

    parser = requestparse(['indicators', 'type', 'host_identifier', "query_name", "start", "limit"],
                          [str, str, str, str, int, int],
                          ['Hashed Threat indicators', 'type of threat (md5/sha256)', 'host_identifier of the node',
                           "query_name", "start", "limit"],
                          [True, True, False, False, False, False],
                          [None, PolyLogyxServerDefaults.search_supporting_columns, None, None, None, None],
                          [None, None, None, None, 0, 100])

    
    def post(self):
        args = self.parser.parse_args()

        indicator_type = args['type']
        indicators = [indicator for indicator in args['indicators'].strip().split(',') if indicator]
        query_name = args['query_name']
        host_identifier = args['host_identifier']
        start = args['start']
        limit = args['limit']

        results = hunt_through_indicators(indicators, indicator_type, host_identifier, query_name, start, limit)
        return marshal(prepare_response(results[0], results[1], results[2]), parent_wrappers.common_response_wrapper)


@api.resource('/hunt-upload/export', endpoint="export_hunt_file_upload")
class ExportHuntFileUpload(Resource):
    """
        Export Hunt results through the file uploaded
    """

    from werkzeug import datastructures
    parser = requestparse(['file', 'type', 'host_identifier', "query_name"],
                          [datastructures.FileStorage, str, str, str],
                          ['Threat file', 'type of hunt (md5/sha256/domain name)', 'host_identifier of the node',
                           "query_name"],
                          [True, True, True, True],
                          [None, PolyLogyxServerDefaults.search_supporting_columns, None, None],
                          [None, None, None, None])

    @validate_file_size
    def post(self):
        args = self.parser.parse_args()
        data = None
        message = None
        status = "failure"
        lines = None

        indicator_type = args['type']
        file = args['file']
        query_name = args['query_name']
        host_identifier = args['host_identifier']
        nodes = get_nodes_for_host_id(host_identifier)

        try:
            lines = [line.decode('utf-8').replace('\n', '').replace('\r', '') for line in file.readlines() if line.decode('utf-8').replace('\n', '').replace('\r', '')]
        except Exception as e:
            message = "We are unable to read this file with this format!"
            current_app.logger.error("Unable to read file of this format - {0}".format(str(e)))
        if lines is not None:
            if nodes:
                try:
                    results = common_dao.result_log_query_for_export(lines, indicator_type, [node.id for node in nodes],
                                                                        query_name)
                    results = [r for r, in results]
                    bio = result_log_columns_export_using_query_set(results)
                    file_data = send_file(
                        bio,
                        mimetype='text/csv',
                        as_attachment=True,
                        attachment_filename='hunt_query_results.csv'
                    )
                    return file_data
                except Exception as e:
                    data = []
                    message = str(e)
            else:
                message = "Host identifier given is wrong!"

        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/search', endpoint="search")
class Search(Resource):
    """
        Searches in result log table for the payload given
    """
    parser = requestparse(['conditions', 'host_identifier', 'query_name', 'start', 'limit'],
                          [dict, str, str, int, int],
                          ["conditions to search for", 'host_identifier of the node', 'query name', 'start', 'limit'],
                          [True, False, False, False, False])

    
    def post(self):
        from polylogyx.blueprints.v1.utils import SearchParserOld as SearchConditionsParser
        args = self.parser.parse_args()
        host_identifier = args['host_identifier']
        query_name = args['query_name']
        start = args['start']
        limit = args['limit']
        conditions = args['conditions']
        if not start:
            start = 0
        if not limit:
            limit = 100

        data = None
        message = None
        status = "failure"
        try:
            search_rules = SearchConditionsParser()
            root = search_rules.parse_group(conditions)
        except Exception as e:
            message = str(e)
            return marshal(prepare_response(message, status),
                           parent_wrappers.common_response_wrapper)

        try:
            query_filter = root.run('', [], 'result_log')
        except Exception as e:
            return marshal(prepare_response("Conditions passed are not correct! Please check once and try again! -- {}"
                                            .format(str(e)), status),
                           parent_wrappers.common_response_wrapper)

        if not host_identifier:
            search_results = common_dao.result_log_search_results_count(query_filter)
            output_list_data = []
            for search_result in search_results:
                data_dict = hosts_dao.get_host_id_and_name_by_node_id(search_result[0])
                query_count_pair = {"query_name": search_result[1], "count": search_result[2]}
                is_matched = False
                for host_result_log_item in output_list_data:
                    if data_dict['host_identifier'] == host_result_log_item['host_identifier']:
                        is_matched = True
                        if 'queries' in host_result_log_item:
                            host_result_log_item['queries'].append(query_count_pair)
                        else:
                            host_result_log_item['queries'] = []
                if not is_matched:
                    data_dict['queries'] = [query_count_pair]
                    output_list_data.append(data_dict)

            message = "Successfully fetched the data through the payload given"
            status = "success"
            data = output_list_data
            if not data:
                data = {}

        else:
            if not query_name:
                message = "Please provide the query name"
            else:
                qs = common_dao.result_log_search_results(query_filter,
                                                          [node.id for node in get_nodes_for_host_id(host_identifier)],
                                                          query_name, start, limit)
                data = {'count': qs['count'], 'results': [data_elem[0] for data_elem in qs['results']]}
                message = "Successfully fetched the data through the payload given"
                status = "success"

        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/indicators/upload', endpoint="indicators_file_upload")
class IndicatorsUpload(Resource):
    """
        Hunting Indicators uploaded
    """

    from werkzeug import datastructures
    parser = requestparse(['file', 'indicator_type', 'host_identifier', "query_name", "start", "limit", 'duration',
                           'type', 'date'],
                          [datastructures.FileStorage, str, str, str, int, int, int, int, str],
                          ['Threat file', 'type of indicator (md5/sha256/domain name)', 'host_identifier of the node',
                           "query_name", "start", "limit", 'duration', 'type', 'date'],
                          [True, True, False, False, False, False, False, False, False],
                          [None, PolyLogyxServerDefaults.search_supporting_columns, None, None, None, None,
                           [1, 2, 3, 4], [1, 2], None],
                          [None, None, None, None, 0, 100, 3, 2, dt.datetime.utcnow().strftime('%Y-%m-%d')])

    @validate_file_size
    def post(self):
        args = self.parser.parse_args()
        data = None
        message = None
        status = "failure"
        lines = None

        indicator_type = args['indicator_type']
        file = args['file']
        query_name = args['query_name']
        host_identifier = args['host_identifier']
        start = args['start']
        limit = args['limit']

        try:
            start_date, end_date = get_start_date_end_date(args)
        except Exception as e:
            current_app.logger.error('Date format passed is invalid! - {}'.format(str(e)))
            return abort(400, {'message': 'Date format passed is invalid!'})

        try:
            lines = [line.decode('utf-8').replace('\n', '').replace('\r', '') for line in file.readlines() if line.decode('utf-8').replace('\n', '').replace('\r', '')]
        except Exception as e:
            message = "We are unable to read this file with this format! - {}".format(str(e))
            current_app.logger.error("Unable to read file of this format - {0}".format(str(e)))
        if lines is not None:
            results = filter_results_through_indicators(lines, indicator_type, host_identifier, query_name, start,
                                                        limit, start_date, end_date)
        else:
            results = {"message": message, "status": status, "data": data}
        return marshal(results, parent_wrappers.common_response_wrapper)


def filter_results_through_indicators(lines, indicator_type, host_identifier, query_name, start, limit, start_date,
                                      end_date):
    status = "failure"
    data = None
    nodes = []
    if host_identifier:
        nodes = get_nodes_for_host_id(host_identifier)
    try:
        data = common_dao.results_with_indicators_filtered(lines, indicator_type, [node.id for node in nodes],
                                                           query_name, start, limit, start_date, end_date)
        message = "Successfully fetched the results through the hunt"
        status = "success"
    except Exception as e:
        message = "Unable to search for given indicators - {}".format(str(e))

    return {"message": message, "status": status, "data": data}


@api.resource('/indicators/upload/export', endpoint="export_result_for_indicators_uploaded")
class ExportIndicatorsUpload(Resource):
    """
        Exports results of Hunting Indicators uploaded
    """

    from werkzeug import datastructures
    parser = requestparse(['file', 'indicator_type', 'host_identifier', "query_name", 'duration', 'type', 'date'],
                          [datastructures.FileStorage, str, str, str, int, int, str],
                          ['Threat file', 'type of indicator (md5/sha256/domain name)', 'host_identifier of the node',
                           "query_name", 'duration', 'type', 'date'],
                          [True, True, False, False, False, False, False],
                          [None, PolyLogyxServerDefaults.search_supporting_columns, None, None,
                           [1, 2, 3, 4], [1, 2], None],
                          [None, None, None, None, 3, 2, dt.datetime.utcnow().strftime('%Y-%m-%d')])

    @validate_file_size
    def post(self):
        args = self.parser.parse_args()
        data = None
        message = None
        status = "failure"
        lines = None

        indicator_type = args['indicator_type']
        file = args['file']
        query_name = args['query_name']
        host_identifier = args['host_identifier']
        nodes = get_nodes_for_host_id(host_identifier)
        try:
            start_date, end_date = get_start_date_end_date(args)
        except Exception as e:
            current_app.logger.error('Date format passed is invalid! - {}'.format(str(e)))
            return abort(400, {'message': 'Date format passed is invalid!'})
        try:
            lines = [line.decode('utf-8').replace('\n', '').replace('\r', '') for line in file.readlines() if line.decode('utf-8').replace('\n', '').replace('\r', '')]
        except Exception as e:
            message = "We are unable to read this file with this format! - {}".format(str(e))
            current_app.logger.error("Unable to read file of this format - {0}".format(str(e)))
        if lines is not None:
            try:
                results = common_dao.results_with_indicators_filtered_to_export(lines, indicator_type,
                                                                                [node.id for node in nodes], query_name,
                                                                                start_date, end_date)
                results = [r for r, in results]
                bio = result_log_columns_export_using_query_set(results)
                file_data = send_file(
                  bio,
                  mimetype='text/csv',
                  as_attachment=True,
                  attachment_filename='hunt_query_results.csv'
                )
                return file_data
            except Exception as e:
                data = []
                message = "Unable to export results for given indicators - {}".format(str(e))

        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/activity/search', endpoint="results_search")
class ActivitySearch(Resource):
    """
        Searches in result log table for the payload given
    """
    parser = requestparse(['conditions', 'host_identifier', 'query_name', 'start', 'limit', 'duration', 'type', 'date'],
                          [dict, str, str, int, int, int, int, str],
                          ["conditions to search for", 'host_identifier of the node', 'query name', 'start', 'limit',
                           'duration', 'type', 'date'],
                          [True, False, False, False, False, False, False, False],
                          [None, None, None, None, None, [1, 2, 3, 4], [1, 2], None],
                          [None, None, None, 0, 100, 3, 2, dt.datetime.utcnow().strftime('%Y-%m-%d')])
    
    def post(self):
        args = self.parser.parse_args()
        host_identifier = args['host_identifier']
        query_name = args['query_name']
        start = args['start']
        limit = args['limit']
        conditions = args['conditions']

        status = "failure"

        try:
            start_date, end_date = get_start_date_end_date(args)
        except Exception as e:
            current_app.logger.error('Date format passed is invalid! - {}'.format(str(e)))
            return abort(400, {'message': 'Date format passed is invalid!'})

        try:
            search_rules = SearchParser()
            root = search_rules.parse_group(conditions)
        except UnSupportedSearchColumn as e:
            return marshal(prepare_response(str(e), status),
                           parent_wrappers.common_response_wrapper)
        except Exception as e:
            message = str(e)
            return marshal(prepare_response(message, status),
                           parent_wrappers.common_response_wrapper)

        try:
            query_filter = root.run('', [], 'result_log')
        except Exception as e:
            current_app.logger.error(
                "Conditions passed are not correct! Please check once and try again! - {}".format(str(e)))
            return marshal(prepare_response("Conditions passed are not correct! Please check once and try again! - {}"
                                            .format(str(e)), status), parent_wrappers.common_response_wrapper
                          )

        data = common_dao.result_log_search_query(query_filter,
                                                  [node.id for node in get_nodes_for_host_id(host_identifier)],
                                                  query_name, start, limit, start_date, end_date)
        message = "Successfully fetched the data through the payload given"
        status = "success"

        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/queryresult/delete', endpoint="delete_queryresult")
class DeleteQueryResult(Resource):
    """
        Deleting the scheduled query result for the no.of days given will be done here
    """

    def post(self):
        # Deprecated and is no longer supported
        current_app.logger.info("This api has been removed")
        abort(410, "This api has been removed, \
                   Please check the REST API documentation for more information about the new APIs")


@api.resource('/schedule_query/export', endpoint="schedule_query_export")
class ExportScheduleQueryCSV(Resource):
    """
        Exports schedule query results into a csv file
    """
    parser = requestparse(['query_name', 'host_identifier'], [str, str],
                          ["name of the query", "host identifier of the node"], [True, True])
    
    def post(self):
        all_args = self.parser.parse_args()

        query_name = all_args['query_name']
        host_identifier = all_args['host_identifier']
        node_id = get_node_id_by_host_id(host_identifier)
        if not node_id:
            message = "Node does not exists for the id given"
        else:
            record_query = common_dao.record_query(node_id, query_name)
            results = [r for r, in record_query]
            if not results:
                message = "Results can't be retrieved for the Payload given! May be data is empty"
            else:
                bio = result_log_columns_export_using_query_set(results)
                file_data = send_file(
                    bio,
                    mimetype='text/csv',
                    as_attachment=True,
                    attachment_filename='query_results.csv'
                )
                return file_data
        return marshal(prepare_response(message, "failure"),
                       parent_wrappers.common_response_wrapper)


@api.resource('/options/add', endpoint="add_options")
class AddOption(Resource):
    """
        Add Options Used by PolyLogyx server
    """
    parser = requestparse(['option'], [dict], ["option data"], [True])

    @admin_required
    def post(self):
        # Deprecated and is no longer supported
        current_app.logger.info("This api has been removed")
        abort(410, "This api has been removed, \
                   Please check the REST API documentation for more information about the new APIs")


@api.resource('/options', endpoint="_options")
class GetOption(Resource):
    """
        Get Options Used by PolyLogyx server
    """

    def get(self):
        # Deprecated and is no longer supported
        current_app.logger.info("This api has been removed")
        abort(410, "This api has been removed, \
                   Please check the REST API documentation for more information about the new APIs")
