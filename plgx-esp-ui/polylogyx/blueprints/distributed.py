from sqlalchemy import or_
import json
import datetime as dt

from flask import jsonify, request, current_app
from flask_restplus import Namespace, Resource, marshal

from polylogyx.models import db
from .utils import *
from polylogyx.utils import require_api_key, create_tags, get_tags, validate_osquery_query
from polylogyx.dao import nodes_dao as nodedao
from polylogyx.dao import distributed_dao as dao
from polylogyx.wrappers import query_wrappers as wrapper
from polylogyx.wrappers import parent_wrappers as parentwrapper


ns = Namespace('distributed', description='distributed query related operations')

# Distributed Query section


@require_api_key
@ns.route('/add', endpoint = 'distributed_add')
@ns.doc(params={'query':'query', 'tags': 'tags', 'nodes':'nodes', 'description':'description for the post method'})
class DistributedQueryClass(Resource):
    """
    Retrieve an osquery configuration for a given node.
    returns: an osquery configuration file
    """
    parser = requestparse(['query','tags','nodes','description'],[str, str, str, str],['query','tags list string seperated by commas','nodes list by comma separated','description'],[True, False, False, False])

    @ns.expect(parser)
    def post(self, node=None):
        from manage import declare_queue

        args = self.parser.parse_args()  # need to exists for input payload validation
        onlineNodes = 0

        sql = args['query']
        if not validate_osquery_query(sql):
            message = u'Field must contain valid SQL to be run against osquery tables'
        else:
            status = 'success'
            message = 'Successfully send the distributed query'
            tag_all = 'all'
            current_app.logger.info(
                "%s - %s checking in for distributed query",
                request.remote_addr, node
            )
            # all nodes get this query
            nodes = []
            tags = []
            if args['tags']:
                tags = args['tags'].split(',')
            if args['nodes']:
                nodeKeyList = args['nodes'].split(',')
            else:
                nodeKeyList = []

            if not nodeKeyList and not tags:
                # all nodes get this query
                nodes = nodedao.get_all_nodes()

            if nodeKeyList:
                nodes = nodedao.extend_nodes_by_node_key_list(nodeKeyList)
            if tags:
                nodes = nodedao.extend_nodes_by_tag(tags)
            query = dao.add_distributed_query(sql,args['description'])
            win_sql_query = None

            typed_query = query.sql
            query_windows_specific = False
            if 'win_file_events' in query.sql or 'win_process_events' in query.sql:
                win_sql_query = typed_query
                query_windows_specific = True
            elif 'file_events' in query.sql:
                win_sql_query = query.sql.replace('file_events', 'win_file_events')
            elif 'process_events' in query.sql:
                win_sql_query = query.sql.replace('process_events', 'win_process_events')

            for node in nodes:
                if node.node_is_active():
                    onlineNodes += 1
                    task = dao.create_distributed_task_obj(node, query)
                    if node.platform == 'windows':
                        task.sql = win_sql_query
                    if not (node.platform != 'windows' and query_windows_specific):
                        db.session.add(task)
            else:
                db.session.commit()
            declare_queue(query.id)
            if onlineNodes == 0:
                message = 'No active node present'
            else:
                return marshal({'query_id': query.id}, wrapper.add_query_wrapper)

        return marshal(prepare_response(message), parentwrapper.failure_response_parent)