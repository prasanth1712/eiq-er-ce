from flask_restplus import Namespace, Resource

from polylogyx.blueprints.v1.utils import *
from polylogyx.utils import validate_osquery_query
from polylogyx.dao.v1 import distributed_dao, hosts_dao
from polylogyx.wrappers.v1 import parent_wrappers

ns = Namespace('distributed', description='distributed query related operations')


@ns.route('/add', endpoint='distributed_add')
class DistributedQueryClass(Resource):
    """
        Adds distributed query.
        returns: query_id, nodes(host identifiers and hostnames), no.of online nodes
    """
    parser = requestparse(['query', 'tags', 'nodes', 'os_name', 'description'],
                          [str, str, str, list, str],
                          ['query', 'tags list string separated by commas',
                           'nodes list by comma separated', 'list of os names', 'description'],
                          [True, False, False, False, False])

    @ns.expect(parser)
    def post(self):
        from manage import declare_queue
        from polylogyx.utils import check_for_rabbitmq_status
        args = self.parser.parse_args()
        online_nodes = 0
        hosts_array = []
        sql = args['query']
        if not args['nodes'] and not args['tags'] and not args['os_name']:
            message = "At least one of Nodes/tags/Os name is required!"
            current_app.logger.info("At least one of Nodes/tags/Os name is required!")
        elif not validate_osquery_query(sql):
            message = "Field must contain valid SQL to be run against OSQuery tables!"
            current_app.logger.info("Field must contain valid SQL to be run against OSQuery tables!")
        elif not check_for_rabbitmq_status():
            message = 'Something went wrong, please try again!'
            current_app.logger.critical('Rabbitmq server is down!')
        else:
            status = 'success'
            message = 'Distributed query has been sent successfully'
            nodes = []
            tags = []
            if args['tags']:
                tags = args['tags'].split(',')
            if args['nodes']:
                node_key_list = args['nodes'].split(',')
            else:
                node_key_list = []
            if args['os_name']:
                nodes.extend([node for node in hosts_dao.get_hosts_from_os_names(args['os_name'])])

            if node_key_list:
                for node in hosts_dao.extend_nodes_by_node_key_list(node_key_list):
                    if node not in nodes:
                        nodes.append(node)
            if tags:
                for node in hosts_dao.extend_nodes_by_tag(tags):
                    if node not in nodes:
                        nodes.append(node)
            query = distributed_dao.add_distributed_query(sql, args['description'])

            if nodes:
                for node in nodes:
                    if node.node_is_active():
                        online_nodes += 1
                        hosts_array.append({"host_identifier": node.host_identifier, "hostname": node.display_name,
                                            "node_id": node.id})
                        task = distributed_dao.create_distributed_task_obj(node, query)
                        db.session.add(task)
                else:
                    db.session.commit()
            declare_queue(query.id)
            if online_nodes == 0:
                current_app.logger.info('No active node present from the list of nodes selected for distributed query')
                message = 'No active node present'
            else:
                current_app.logger.info("Distributed Query {0} is added to the hosts {1}".format(query.id,
                                        [host['host_identifier'] for host in hosts_array]))
                return marshal(prepare_response(message, status, {'query_id': query.id, 'onlineNodes': online_nodes,
                                                                  'online_nodes_details': hosts_array}),
                               parent_wrappers.common_response_wrapper)
        return marshal(prepare_response(message), parent_wrappers.failure_response_parent)
