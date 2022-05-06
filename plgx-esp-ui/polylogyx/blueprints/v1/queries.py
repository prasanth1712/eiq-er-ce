from flask_restplus import Namespace, Resource, inputs
from flask import abort

from polylogyx.blueprints.v1.utils import *
from polylogyx.utils import validate_osquery_query, create_tags, is_number_positive
from polylogyx.dao.v1 import queries_dao, tags_dao
from polylogyx.wrappers.v1 import parent_wrappers, query_wrappers
from polylogyx.authorize import admin_required

ns = Namespace('queries', description='queries related operations')


@ns.route('', endpoint="list queries")
class QueriesList(Resource):
    """
        Lists all queries of the Nodes
    """
    parser = requestparse(["start", "limit", "searchterm"], [int, int, str],
                          ["start", "limit", "searchterm"], [False, False, False],
                          [None, None, None], [None, None, ''])

    @ns.expect(parser)
    @ns.marshal_with(parent_wrappers.common_response_wrapper)
    def post(self):
        args = self.parser.parse_args()
        queryset = queries_dao.get_all_queries(args['searchterm']).offset(args['start']).limit(args['limit']).all()
        data = marshal(queryset, query_wrappers.query_wrapper)
        for i in range(len(data)):
            data[i]['tags'] = [tag.to_dict() for tag in queryset[i].tags]
            data[i]['packs'] = [pack.name for pack in queryset[i].packs]
        message = "Successfully fetched the queries info!"
        status = "success"
        if not data:
            data = []
        data = {'count': queries_dao.get_all_queries(args['searchterm']).count(),
                'total_count': queries_dao.get_total_count(),
                'results': data}
        return prepare_response(message, status, data)


@ns.route('/packed', endpoint="list packed queries")
class PackedQueriesList(Resource):
    """
        List all packed queries of the Nodes
    """

    parser = requestparse(["start", "limit", "searchterm"], [int, int, str],
                          ["start", "limit", "searchterm"], [False, False, False],
                          [None, None, None], [None, None, ''])

    @ns.expect(parser)
    @ns.marshal_with(parent_wrappers.common_response_wrapper)
    def post(self):
        args = self.parser.parse_args()
        queryset = queries_dao.get_all_packed_queries(args['searchterm']).offset(args['start'])\
            .limit(args['limit']).all()
        data = marshal(queryset, query_wrappers.query_wrapper)
        for i in range(len(data)):
            data[i]['tags'] = [tag.to_dict() for tag in queryset[i].tags]
            data[i]['packs'] = [pack.name for pack in queryset[i].packs]
        message = "Successfully fetched the packed queries info"
        status = "success"
        if not data:
            data = []
        data = {'count': queries_dao.get_all_packed_queries(args['searchterm']).count(),
                'total_count': queries_dao.get_total_packed_queries_count(),
                'results': data}
        return prepare_response(message, status, data)


@ns.route('/<int:query_id>', endpoint="query by id")
class QueryById(Resource):
    """
        Returns the query info for the given query id
    """

    def get(self, query_id):
        if query_id:
            query_qs = queries_dao.get_query_by_id(query_id)
            if query_qs:
                query = marshal(query_qs, query_wrappers.query_wrapper)
                query['tags'] = [tag.to_dict() for tag in query_qs.tags]
                query['packs'] = [pack.name for pack in query_qs.packs]
                return marshal(prepare_response("Successfully fetched the query info for the given id",
                                                "success", query),
                               parent_wrappers.common_response_wrapper)
            else:
                message = "Query with this id does not exist"
        else:
            message = "Missing query id"
        return marshal(prepare_response(message), parent_wrappers.failure_response_parent)


@ns.route('/<int:query_id>', endpoint="edit query")
class EditQueryById(Resource):
    """
        Edit query by its id
    """
    parser = requestparse(
        ['name', 'query', 'interval', 'tags', 'platform', 'version', 'description', 'value', 'snapshot', 'packs'],
        [str, str, int, str, str, str, str, str, str, str],
        ["name of the query", "query", "interval of the query", "list of comma separated tags of the query to add",
         "platform(all/windows/linux/darwin/freebsd/posix)", "version",
         "description", "value", "snapshot('true'/'false')", "list of comma separated pack names to add"],
        [True, True, True, False, False, False, False, False, False, False],
        [None, None, None, None, ["all", "windows", "linux", "darwin", "freebsd", "posix"], None, None, None,
         ['true', 'false'], None],
        [None, None, None, None, None, None, None, None, "true", None])

    @admin_required
    @ns.expect(parser)
    def post(self, query_id):
        args = self.parser.parse_args()
        if not args['name']:
            abort(400, "Please provide valid name!")
        elif not args['query']:
            abort(400, "Please provide valid SQL!")
        else:
            if args['snapshot'] == "true":
                args['snapshot'] = True
            else:
                args['snapshot'] = False
            if args['tags']:
                args['tags'] = args['tags'].split(',')
            else:
                args['tags'] = []
            if query_id:
                query = queries_dao.get_query_by_id(query_id)
                if query:
                    if validate_osquery_query(args['query']):
                        query_tags = list(query.tags)
                        query_packs = list(query.packs)
                        query = queries_dao.edit_query_by_id(query, args)
                        query_tags.extend(list(query.tags))
                        current_app.logger.info("Query '{0}' has been updated with the payload given!".format(query))
                        return marshal(prepare_response("Successfully updated the query for the given id", "success",
                                                        marshal(query, query_wrappers.query_wrapper)),
                                       parent_wrappers.common_response_wrapper)
                    else:
                        message = "Query is not a valid SQL!"
                else:
                    message = "Query with this id does not exist"
            else:
                message = "Missing query id"
            return marshal(prepare_response(message), parent_wrappers.failure_response_parent)


@ns.route('/add', endpoint="add query")
class AddQuery(Resource):
    """
        Add queries
    """
    parser = requestparse(
        ['name', 'query', 'interval', 'tags', 'platform', 'version', 'description', 'value', 'snapshot', 'packs'],
        [str, str, int, str, str, str, str, str, str, str],
        ["name of the query", "query", "interval of the query", "list of comma separated tags of the query to add",
         "platform(all/windows/linux/darwin/freebsd/posix)", "version",
         "description", "value", "snapshot('true'/'false')", "list of comma separated pack names to add"],
        [True, True, True, False, False, False, False, False, False, False],
        [None, None, None, None, ["all", "windows", "linux", "darwin", "freebsd", "posix"], None, None, None,
         ["true", "false"], None],
        [None, None, None, None, None, None, None, None, "true", None])

    @admin_required
    @ns.expect(parser)
    def post(self):
        from polylogyx.dao.v1 import packs_dao
        args = self.parser.parse_args()

        name = args['name']
        sql = args['query']
        interval = args['interval']
        if not args['name']:
            abort(400, "Please provide valid name!")
        elif not args['query']:
            abort(400, "Please provide valid SQL!")
        else:
            if args['snapshot'] == "true":
                args['snapshot'] = True
            else:
                args['snapshot'] = False

            if args['tags']:
                tags = args['tags'].split(',')
            else:
                tags = args['tags']
            packs = []
            if args['packs']:
                packs = args['packs'].split(',')
            query = queries_dao.get_query_by_name(name)
            if query:
                message = 'Query with this name already exists'
            elif not validate_osquery_query(sql):
                message = ('Invalid osquery query: "{0}"'.format(args['query']))
            elif not is_number_positive(interval):
                message = 'Interval provided is not valid! Please provide an interval greater than 0'
            else:
                query = queries_dao.create_query_obj(name, sql, interval, args['platform'], args['version'],
                                                     args['description'], args['value'], 100, snapshot=args['snapshot'])
                if tags:
                    query.tags = create_tags(*tags)
                if packs:
                    packs_list = []
                    for pack_name in packs:
                        pack = packs_dao.get_pack_by_name(pack_name)
                        if pack:
                            packs_list.append(pack)
                    query.packs = packs_list
                query.save()
                current_app.logger.info("A new Query '{0}' has been added with name '{1}'".format(query, query.name))
                return marshal({'query_id': query.id}, query_wrappers.add_query_wrapper)
            return marshal(prepare_response(message), parent_wrappers.failure_response_parent)


@ns.route('/<int:query_id>/tags', endpoint='query tags list')
class ListTagsOfQuery(Resource):
    """
        Resource for tags of a Query
    """
    parser = requestparse(['tag'], [str], ["tag to add/remove for the query"], [True])

    def get(self, query_id=None):
        """
            Lists tags of a Query by its id
        """
        status = 'failure'
        if query_id:
            query = queries_dao.get_query_by_id(query_id)
        else:
            query = None
        if not query:
            message = "Query id passed it not correct"
            data = None
        else:
            data = [tag.value for tag in query.tags]
            status = "success"
            message = "Successfully fetched the tags of query"
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper, skip_none=True)

    @admin_required
    @ns.expect(parser)
    def post(self, query_id=None):
        """
            Adds tags of a Query by its id
        """
        args = self.parser.parse_args()
        status = 'failure'

        if query_id:
            query = queries_dao.get_query_by_id(query_id)
        else:
            query = None
        if query:
            tag = args['tag'].strip()
            if not tag:
                message = "Tag provided is invalid!"
            else:
                tag = tags_dao.create_tag_obj(tag)
                query.tags.append(tag)
                query.save()
                status = "success"
                message = "Successfully created tags to query"
                current_app.logger.info("Tag '{0}' has been added to the Query '{1}'".format(tag, query))
        else:
            message = "query id passed it not correct"

        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)

    @admin_required
    @ns.expect(parser)
    def delete(self, query_id=None):
        """
            Removes tags of a Query by its id
        """
        args = self.parser.parse_args()
        status = 'failure'

        if query_id:
            query = queries_dao.get_query_by_id(query_id)
        else:
            query = None
        if query:
            tag = args['tag'].strip()
            tag = tags_dao.get_tag_by_value(tag)
            if tag:
                if queries_dao.is_tag_of_query(query, tag):
                    query.tags.remove(tag)
                    query.save()
                    message = "Successfully removed tags from query"
                    status = "success"
                    current_app.logger.info("Tag '{0}' has been removed from the Query '{1}'".format(tag, query))
                else:
                    message = "Tag provided is not in query's tag list, Please check tag once again"
            else:
                message = "Tag provided doesn't exists"
        else:
            message = "Query id name passed it not correct"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/<string:query_name>/delete', endpoint='query removed')
@ns.route('/<int:query_id>/delete', endpoint='query removed by id')
class QueryRemoved(Resource):

    @admin_required
    def delete(self, query_name=None, query_id=None):
        status = "failure"
        message = "Query is not available with this query_name or query_id"
        query = None
        if query_id:
            query = queries_dao.get_query_by_id(query_id)

        if query_name:
            query = queries_dao.get_query_by_name(query_name)

        if query:
            current_app.logger.info("Query {} is requested to delete".format(query.name))
            query_tags = query.tags
            db.session.delete(query)
            db.session.commit()
            message = "Successfully Removed the query"
            status = "Success"
            current_app.logger.warning("Query {} has been deleted!".format(query))
            return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)
