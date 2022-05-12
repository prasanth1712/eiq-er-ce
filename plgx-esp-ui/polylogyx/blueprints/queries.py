from flask import jsonify, request
from flask_restplus import reqparse, Namespace, Resource, marshal

import json

from .utils import *
from polylogyx.utils import require_api_key, validate_osquery_query, create_tags, get_tags
from polylogyx.dao import queries_dao as dao
from polylogyx.wrappers import query_wrappers as wrapper
from polylogyx.wrappers import parent_wrappers as parentwrapper


ns = Namespace('queries', description='queries related operations')


parser = reqparse.RequestParser()
nodes_post = parser.copy()


@require_api_key
@ns.route('/', endpoint = "list_queries")
@ns.doc(params={})
class QueriesList(Resource):
    """List all queries of the Nodes"""

    @ns.marshal_with(parentwrapper.common_response_wrapper)
    def get(self):
        """returns API response of list of queries info"""
        queryset = dao.get_all_queries()
        data = marshal(queryset,wrapper.query_wrapper)
        for i in range(len(data)):
            data[i]['tags'] = [tag.to_dict() for tag in queryset[i].tags]
        message = "successfully fetched the queries info"
        if not data: message = "there is no data to show"
        return prepare_response(message,"success",data)


@require_api_key
@ns.route('/packs', endpoint = "list_packed_queries")
@ns.doc(params={})
class PackedQueriesList(Resource):
    """List all packed queries of the Nodes"""

    @ns.marshal_with(parentwrapper.common_response_wrapper)
    def get(self):
        """returns API response of list of packed queries info"""
        queryset = dao.get_all_packed_queries()
        data = marshal(queryset,wrapper.query_wrapper)
        for i in range(len(data)):
            data[i]['tags'] = [tag.to_dict() for tag in queryset[i].tags]
            data[i]['packs'] = [pack.name for pack in queryset[i].packs]
        message = "successfully fetched the packed queries info"
        if not data: message = "there is no data to show"
        return prepare_response(message,"success",data)


@require_api_key
@ns.route('/<int:query_id>', endpoint = "query_by_id")
@ns.doc(params={'query_id': 'id of the query'})
class QueryById(Resource):
    """ responses the query info for the given query id"""

    def get(self, query_id):
        if query_id:
            query_qs = dao.get_query_by_id(query_id)
            if query_qs:
                query=marshal(query_qs,wrapper.query_wrapper)
                query['tags'] = [tag.to_dict() for tag in query_qs.tags]
                query['packs'] = [pack.name for pack in query_qs.packs]
                return marshal(prepare_response("successfully fecthed the query info for the given id","success",query) , parentwrapper.common_response_wrapper)
            else:
                message = "Query with this id does not exist"
        else:
            message = "Missing query id"
        return marshal(prepare_response(message), parentwrapper.failure_response_parent)


@require_api_key
@ns.route('/<int:query_id>', endpoint = "edit_query")
@ns.doc(params={'query_id': 'id of the query'})
class EditQueryById(Resource):
    """edit query by its id"""

    def post(self, query_id):
        if query_id:
            query = dao.get_query_by_id(query_id)
            if query:
                return marshal(prepare_response("successfully fecthed the query info for the given id","success",marshal(query,wrapper.query_wrapper)) , parentwrapper.common_response_wrapper)
            else:
                message = "Query with this id does not exist"
        else:
            message = "Missing query id"
        return marshal(prepare_response(message), parentwrapper.failure_response_parent)


@require_api_key
@ns.route('/add', endpoint = "add_query")
@ns.doc(params={'name': 'name of the query', 'query':"query", 'interval':"interval for the query", 'tags':"tags of the query", 'platform':"platform", 'version':"version", 'description':"description", 'value':"value", 'snapshot':"snapshot"})
class AddQuery(Resource):
    """add queries"""
    parser = requestparse(
        ['name', 'query', 'interval', 'tags', 'platform', 'version', 'description', 'value', 'snapshot'],
        [str, str, int, str, str, str, str, str, bool],
        ["name of the query", "query", "interval of the query", "list of comma separated tags of the query to add", "platform", "version",
         "description", "value", "snapshot"],
        [True, True, True, False, False, False, False, False, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation

        name = args['name']
        sql = args['query']
        interval = args['interval']
        tags = args['tags'].split(',')

        query = dao.get_query_by_name(name)
        if query:
            message = 'Query with this name already exists'
        elif not validate_osquery_query(sql):
            message = ('Invalid osquery query: "{0}"'.format(args['query']))
        else:
            query = dao.create_query_obj(name, sql, interval, args['platform'], args['version'], args['description'],
                                       args['value'], 100, snapshot=args['snapshot'])
            if tags:
                query.tags = create_tags(*tags)
            query.save()
            return marshal({'query_id': query.id}, wrapper.add_query_wrapper)
        return marshal(prepare_response(message), parentwrapper.failure_response_parent)


@require_api_key
@ns.route('/tag/edit', endpoint = "add_tag_to_query")
@ns.doc(params={'query_id': 'id of the query','add_tags':"tags to add", 'remove_tags':"tags to remove"})
class AddTagToQuery(Resource):
    parser = requestparse(['query_id', 'add_tags', 'remove_tags'], [int, str, str],
                          ["id of the query", "list of comma separated tags to add", "list of comma separated tags to remove"], [True, False, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation

        query_id = args['query_id']
        status = 'failure'
        message = None

        add_tags = args['add_tags'].split(',')
        remove_tags = args['remove_tags'].split(',')
        if not (add_tags or remove_tags):
            message = 'Please provide tags'
        else:
            query = dao.get_query_by_id(query_id)
            if not query:
                message = 'Invalid query id. Query with this id does not exist'
            else:
                if add_tags:
                    add_tags = create_tags(*add_tags)
                    for add_tag in add_tags:
                        if not add_tag in query.tags:
                            query.tags.append(add_tag)

                if remove_tags:
                    remove_tags = get_tags(*remove_tags)
                    for remove_tag in remove_tags:
                        if remove_tag in query.tags:
                            query.tags.remove(remove_tag)
                query.save()
                status = 'success'
                message = 'Successfully modified the tag(s)'
        return marshal(prepare_response(message,status), parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/<int:query_id>/tags', endpoint='query_tags_list')
@ns.doc(params={'query_id': 'query id', 'tags': "tags to create to the query"})
class ListTagsOfQuery(Resource):
    """list tags of a query by its query id"""
    parser = requestparse(['tags'], [str], ["list of comma separated tags to be created to the query"])

    def get(self, query_id):
        status = 'failure'
        query = dao.get_query_by_id(query_id)
        if not query:
            message = 'Invalid query id. This query does not exist'
            data = None
        else:
            data = tag_name_format(query.tags)
            status = 'success'
            message = 'Successfully fetched the tag(s)'
        return marshal(prepare_response(message, status, data), parentwrapper.common_response_wrapper, skip_none=True)

    @ns.expect(parser)
    def post(self, query_id):
        args = self.parser.parse_args()  # need to exists for input payload validation
        tags = args['tags'].split(',')
        query = dao.get_query_by_id(query_id)
        if query:
            obj_list = get_tags_list_to_add(tags)
            query.tags.extend(obj_list)
            query.save()
            return marshal(prepare_response('Successfully created the tag(s) to queries', 'success'),
                           parentwrapper.common_response_wrapper, skip_none=True)
        return marshal(prepare_response('Query is not present for the id given!', 'failure'), parentwrapper.common_response_wrapper, skip_none=True)
