from io import BytesIO
import unicodecsv as csv
import json
import datetime as dt

from flask import jsonify, request, send_file
from flask_restplus import Namespace, Resource, marshal

from .utils import *
from polylogyx.utils import require_api_key, create_tags, get_tags
from polylogyx.dao import nodes_dao as dao
from polylogyx.dao import common_dao
from polylogyx.wrappers import node_wrappers as wrapper
from polylogyx.wrappers import parent_wrappers as parentwrapper
from polylogyx.wrappers import resultlog_wrappers as res_wrapper
from polylogyx.wrappers import tag_wrappers as tag_wrapper

from .v1.utils import SearchParser


ns = Namespace('nodes', description='distributed query related operations')


@require_api_key
@ns.route('/', endpoint='all_nodes_info')
class NodeList(Resource):
    """List all Nodes"""
    parser = requestparse(['platform', 'state'],[str, bool],["platform of the node", 'state of the node whether active or in-active'],[False, False])

    @ns.expect(parser)
    @ns.marshal_with(parentwrapper.common_response_wrapper)
    def get(self):
        """returns list of all nodes information"""
        args = self.parser.parse_args()
        queryset = dao.filterNodesByStateActivity(args['platform'], args['state'])
        data = marshal(queryset, wrapper.nodewrapper)
        for i in range(len(data)):
            data[i]['tags'] = [tag.to_dict() for tag in queryset[i].tags]
        message="nodes data fetched successfully"
        if not data: message = "There are no data to be shown and it is empty"
        return prepare_response(message,"success",data)


@require_api_key
@ns.route('/<string:host_identifier>', endpoint='node_info_by_id')
@ns.doc(params={'host_identifier': 'Host identifier of the Node'})
class NodesByHostId(Resource):
    """Get node info by its ID"""
    def get(self, host_identifier):
        """returns specific node info by filtering the object through the host identifier"""
        node_qs = dao.get_node_by_host_identifier(host_identifier)
        if host_identifier:
            if node_qs:
                system_data = marshal(dao.getNodeData(node_qs.id), wrapper.system_data_wrapper, envelope='system_data')
                node = marshal(node_qs, wrapper.nodebyid_wrapper)
                node['system_data'] = system_data
                node['tags'] = [tag.to_dict() for tag in node_qs.tags]
                return marshal(prepare_response("Successfully fetched the node info", 'success', node),parentwrapper.common_response_wrapper, skip_none=True)
            else:
                message="Node with this identifier does not exist"
        else:
            message="Missing host identifier"
        return marshal(prepare_response(message), parentwrapper.failure_response_parent)


# Nodes schedule query results

@require_api_key
@ns.route('/schedule_query/<string:host_identifier>', endpoint='node_schedule_query_by_id')
@ns.doc(params={'host_identifier': 'Host identifier of the Node'})
class NodeScheduleQuery(Resource):
    """returns node schedule query for the host_identifier given"""

    def get(self, host_identifier):
        node = dao.get_node_by_host_identifier(host_identifier)
        status = 'failure'
        data = None
        if not node:
            message = 'Node with this identifier does not exist'
        else:
            try:
                timestamp = request.args.get('timestamp')
                timestamp = dt.datetime.fromtimestamp(float(timestamp))
            except Exception:
                timestamp = dt.datetime.utcnow()
                timestamp -= dt.timedelta(days=30)
            recent = dao.getResultLogs(node, timestamp, 'removed')
            data = [r.to_dict() for r in recent]
            status = 'success'
            message = 'Successfully received schedule query results'
            if not data: message = "There are no data to be shown and it is empty"
        return marshal(prepare_response(message, status, data), parentwrapper.common_response_wrapper)


@require_api_key
@ns.route('/schedule_query/results', endpoint='node_schedule_query_results')
@ns.doc(params={'host_identifier': 'Host identifier of the Node', 'query_name':'query', 'start': 'start count', 'limit':'end count'})
class NodeScheduleQueryResults(Resource):
    """Node schedule query results for the host_identifier,query,start,limit given"""
    parser = requestparse(['host_identifier', 'query_name', 'start', 'limit'], [str, str, int, int], ["host identifier of the node", "query", "start count","end count"], [True, True, False, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()

        host_identifier = args['host_identifier']
        node = dao.get_node_by_host_identifier(host_identifier)
        status = 'failure'
        message = 'Data missing'
        data = None

        if not node:
            message = 'Node with this identifier does not exist'
        else:
            try:
                timestamp = request.args.get('timestamp')
                timestamp = dt.datetime.fromtimestamp(float(timestamp))
            except Exception:
                timestamp = dt.datetime.utcnow()
                timestamp -= dt.timedelta(days=30)

            query_name = args['query_name']
            start = args['start']
            limit = args['limit']

            query = dao.getResultLogsByHostId(node, timestamp, query_name)
            try:
                if not start:
                    start = 0
                if not limit:
                    limit = 0
                if int(start) >= 0 and int(limit) > 0:
                    query = dao.getResultLogsOffsetLimit(node, timestamp, 'removed', query_name, start, limit)
                recent = query.all()
                status = 'success'
                message = 'Successfully received node schedule query results'
                data = marshal(recent,res_wrapper.result_log_wrapper, skip_none=False)
            except:
                message = 'Start and limit must be integer'
            if not data: message = "There are no data to be shown and it is empty"
        return marshal(prepare_response(message,status,data), parentwrapper.common_response_wrapper, skip_none=False)



# Modify Tag section

@require_api_key
@ns.route('/tag/edit', endpoint='node_tag_edit')
@ns.doc(params={'host_identifier': 'Host identifier of the Node', 'add_tags':'list of comma separated tags needed to be added for the node', 'remove_tags': 'list of comma separated tags needed to be removed from the node'})
class EditTagToNode(Resource):
    """edits tags to a node by its host_identifier"""
    parser = requestparse(['host_identifier', 'add_tags', 'remove_tags'], [str, str, str], ["host identifier of the node", "list of comma separated tags needed to be added for the node", "list of comma separated tags needed to be removed from the node"], [True, False, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation
        status = 'failure'
        host_identifier = args['host_identifier']
        add_tags = args['add_tags'].split(',')
        remove_tags = args['remove_tags'].split(',')
        node = dao.get_node_by_host_identifier(host_identifier)
        if not node:
            message = 'Invalid host identifier. This node does not exist'
        else:
            if add_tags:
                add_tags = create_tags(*add_tags)
                for add_tag in add_tags:
                    if not add_tag in node.tags:
                        node.tags.append(add_tag)

            if remove_tags:
                remove_tags = get_tags(*remove_tags)
                for remove_tag in remove_tags:
                    if remove_tag in node.tags:
                        node.tags.remove(remove_tag)

            node.save()
            status = 'success'
            message = 'Successfully modified the tag(s)'

        return marshal(prepare_response(message,status), parentwrapper.common_response_wrapper, skip_none=True)




@require_api_key
@ns.route('/<string:host_identifier>/tags', endpoint='node_tags_list')
@ns.doc(params={'host_identifier': 'Host identifier of the Node', 'tags': 'list of comma separated tags to careate'})
class ListTagsOfNode(Resource):
    """list/creates tags of a node by its host_identifier"""
    parser = requestparse(['tags'], [str], ["list of comma separated tags to create to the node"])

    def get(self, host_identifier):
        status = 'failure'
        node = dao.get_node_by_host_identifier(host_identifier)
        if not node:
            message = 'Invalid host identifier. This node does not exist'
            data = None
        else:
            data = marshal(node.tags,tag_wrapper.tag_name_wrapper)
            status = 'success'
            message = 'Successfully fetched the tag(s)'
        return marshal(prepare_response(message,status,data), parentwrapper.common_response_wrapper, skip_none=True)


    @ns.expect(parser)
    def post(self, host_identifier):
        args = self.parser.parse_args()  # need to exists for input payload validation
        tags = args['tags'].split(',')
        node = dao.get_node_by_host_identifier(host_identifier)
        if not node:
            message = 'Invalid host identifier. This node does not exist'
            data = None
            status = "failure"
        else:
            obj_list = get_tags_list_to_add(tags)
            node.tags.extend(obj_list)
            node.save()
            message = 'Successfully created the tag(s) to node'
            status = 'success'

        return marshal(prepare_response(message,status), parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/search/export', endpoint="nodes_search_export")
@ns.doc(params={})
class ExportNodeSearchQueryCSV(Resource):
    """export node search query to csv"""
    parser = requestparse(['conditions', 'host_identifier'], [dict, str], ["conditions to search for", 'host_identifier of the node'], [True, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        host_identifier = args['host_identifier']
        conditions = args['conditions']
        try:
            node_id = get_node_id_by_host_id(host_identifier)
        except:
            message = "no node found for the host_id given"
            return marshal(prepare_response(message, "failure"), parentwrapper.common_response_wrapper, skip_none=True)
        try:
            search_rules=SearchParser()
            root = search_rules.parse_group(conditions)
        except Exception as e:
            message=str(e)
            return marshal(prepare_response(message, "failure"), parentwrapper.common_response_wrapper, skip_none=True)

        filter = root.run('', [], 'result_log')
        try:
            results = dao.node_result_log_search_results(filter, node_id)
        except:
            message = "Unable to find data for the payload given"
            return marshal(prepare_response(message, "failure"), parentwrapper.common_response_wrapper, skip_none=True)
        output_dict_data = {}
        if results:
            for result in results:
                column=result[2]
                query_name = result[1]
                if query_name in output_dict_data:
                    output_dict_data[query_name].append(column)
                else:
                    output_dict_data[query_name]=[column]

            bio = BytesIO()
            writer = csv.writer(bio)
            if not output_dict_data.keys():
                return marshal(prepare_response("Unable to find data for the payload given", "failure"), parentwrapper.common_response_wrapper, skip_none=True)
            for key in output_dict_data.keys():
                writer.writerow([host_identifier,key,len(output_dict_data[key])])
                query_column_keys = output_dict_data[key][0].keys()
                writer.writerow(query_column_keys)
                for item in output_dict_data[key]:
                    writer.writerow([item.get(query_column_key, '') for query_column_key in query_column_keys])
                writer.writerow(["","",""])

            bio.seek(0)

            response = send_file(
                bio,
                mimetype='text/csv',
                as_attachment=True,
                attachment_filename='node_search_results.csv'
            )
            return response

        else:
            message = "there are no matching results for the payload given"
        return marshal(prepare_response(message, "failure"),parentwrapper.common_response_wrapper, skip_none = True)


@require_api_key
@ns.route('/<string:host_identifier>/queryResult', endpoint = "query result by host id")
@ns.doc(params = {})
class GetQueryResultsOfNode(Resource):
    """get query results for specific node by the host identifier given"""
    parser = requestparse(['start', 'length', 'search[value]', 'columns[0][data]'], [int, int, str, str], ['start', 'length', 'search[value]', 'columns[0][data]'], [True, True, True, False])

    @ns.expect(parser)
    def post(self, host_identifier):
        args = self.parser.parse_args()

        try: node_id = get_node_id_by_host_id(host_identifier)
        except:
            message="there is no node with this host_identifier"
            return marshal(prepare_response(message, "failure"),
                           parentwrapper.common_response_wrapper)

        startPage = 1
        perPageRecords = 100
        nameResult = {}
        names = dao.resultLogNamesQuery(node_id)
        if not 'columns[0][data]' in args.keys(): args['columns[0][data]'] = "Notneeded"
        for name in names:
            nameResult[name[0]] = get_results_by_query(startPage, perPageRecords, node_id, name[0], args)
        if not nameResult: message = "There are no query result data to be shown and it is empty"
        return marshal(prepare_response("Query results are fetched successfully", "success", nameResult), parentwrapper.common_response_wrapper)


@require_api_key
@ns.route('/<string:host_identifier>/activity', endpoint = "node_activity")
@ns.doc(params = {})
class NodeActivity(Resource):
    """returns node activity of a node through its host_identifier"""
    import datetime
    parser = requestparse(['timestamp'],[str],["current time stamp"])

    @ns.expect(parser)
    def post(self,host_identifier):
        args = self.parser.parse_args()

        try:
            node_id = get_node_id_by_host_id(host_identifier)
        except:
            message = "there is no node with this host_identifier"
            return marshal(prepare_response(message, "failure"),
                           parentwrapper.common_response_wrapper)
        if not node_id: return marshal(prepare_response("there is no node with this host_identifier", "failure"),
                                       parentwrapper.common_response_wrapper)

        node = dao.nodeActivityQuery(node_id)
        try:
            timestamp = dt.datetime.strptime(args['timestamp'], '%b %d %Y %I:%M%p')
            #timestamp = dt.datetime.fromtimestamp(float(timestamp))
        except Exception:
            timestamp = dt.datetime.utcnow()
            timestamp -= dt.timedelta(days=30)
        queries_packs = get_queries_or_packs_of_node(node_id)
        queries_packs = [r for r, in queries_packs]
        # recent = node.result_logs.filter(ResultLog.timestamp > timestamp, ResultLog.action != 'removed').all()
        data = {}
        data['node'] = marshal(node,wrapper.node_tag_wrapper)
        data['queries_packs'] = queries_packs
        message = "Node activity is fetched successfully"
        if not data: message = "There are no data to be shown and it is empty"
        return marshal(prepare_response(message, "success", data),parentwrapper.common_response_wrapper,skip_none=True)



