from flask_restful import Resource
from flask import make_response
from polylogyx.blueprints.v1.external_api import api
from polylogyx.blueprints.v1.utils import *
from polylogyx.dao.v1 import hosts_dao, carves_dao
from polylogyx.wrappers.v1 import carve_wrappers, parent_wrappers
from polylogyx.models import DistributedQueryTask, db, CarveSession
from polylogyx.authorize import admin_required
from polylogyx.db.signals import bulk_insert_to_pa


@api.resource('/carves', endpoint='carves list')
class NodeCarvesList(Resource):
    """
        Lists out the carves for a specific node when host_identifier given otherwise returns all carves
    """
    parser = requestparse(['host_identifier', 'start', 'limit', 'searchterm',"column","order_by"], [str, int, int, str,str,str],
                          ["host identifier of the node", "Start Number", "Maximun Number of Carves", "Searchterm","column","order_by"],
                          [False, False, False, False,False,False], [None, None, None, None,['hostname','created_at'],['ASC','asc','Asc','DESC','desc','Desc']], [None, 0, 10, '',None,None])

    
    def post(self):
        from polylogyx.dao.v1.hosts_dao import get_host_name_by_node_id
        carves = None
        status = 'success'
        args = self.parser.parse_args()
        host_identifier = args['host_identifier']

        if host_identifier:
            node = hosts_dao.get_node_by_host_identifier(host_identifier)
            if not node:
                status = 'failure'
                message = 'Node with this identifier does not exists'
            else:
                carves = marshal(carves_dao.get_carves_by_node_id(node.id, args['searchterm']).offset(
                    args['start']).limit(args['limit']).all(), carve_wrappers.carves_wrapper)
                count = carves_dao.get_carves_by_node_id(node.id, args['searchterm']).count()
                total_count = carves_dao.get_carves_total_count(node_id=node.id)
                for carve in carves:
                    carve['hostname'] = get_host_name_by_node_id(carve['node_id'])
                carves = {'count': count, 'results': carves, 'total_count': total_count}
                message = 'Successfully fetched the Carves data'
        else:
            carves = marshal(carves_dao.get_carves_all(args['searchterm'],args['column'],args['order_by']).offset(args['start'])
                             .limit(args['limit']).all(),
                             carve_wrappers.carves_wrapper)
            count = carves_dao.get_carves_all(args['searchterm']).count()
            total_count = carves_dao.get_carves_total_count(node_id=None)
            for carve in carves:
                carve['hostname'] = get_host_name_by_node_id(carve['node_id'])
            carves = {'count': count, 'results': carves, 'total_count': total_count}
            message = 'Successfully fetched the Carves data'
            status = "success"
        return marshal(prepare_response(message, status, carves), parent_wrappers.common_response_wrapper)


@api.resource('/carves/download/<string:session_id>', endpoint='download carves')
class DownloadCarves(Resource):
    """
        Download carves for the session id given
    """
    def get(self, session_id=None):
        status = 'failure'
        if not session_id:
            message = 'Please provide a session id'
        else:
            carve_session = carves_dao.get_carves_by_session_id(session_id)
            if carve_session:
                response = make_response()
                response.headers['Cache-Control'] = 'no-cache'
                response.headers['Content-Type'] = 'application/octet-stream'
                response.headers['X-Accel-Redirect'] = '/esp-ui/carves/' + carve_session.node.host_identifier + '/' + \
                                                       carve_session.archive
                return response
            else:
                message = 'This session id does not exist'
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/carves/query', endpoint='get carves by query id')
class CarveSessionByPostQueryId(Resource):
    """
        Create Carves session by query id
    """
    parser = requestparse(['query_id', 'host_identifier'], [str, str], ["query id", "host_identifier"], [True, True])

    
    def post(self):
        status = 'failure'
        args = self.parser.parse_args()
        host_identifier = args['host_identifier']
        query_id = args['query_id']
        carve_session = {}
        node = hosts_dao.get_node_by_host_identifier(host_identifier)
        if not node:
            message = 'Node with this identifier does not exists'
        else:
            dqt = db.session.query(DistributedQueryTask).filter(
                DistributedQueryTask.distributed_query_id == query_id).filter(
                DistributedQueryTask.node_id == node.id).first()
            if dqt:
                carve_session = db.session.query(CarveSession).filter(CarveSession.request_id == dqt.guid).first()
                if carve_session:
                    carve_session = marshal(carve_session, carve_wrappers.carves_wrapper)
                    status = "success"
                    message = "Successfully fetched the Carve"
                    return marshal(prepare_response(message, status, carve_session),
                                   parent_wrappers.common_response_wrapper)
                else:
                    message = "Carve not started"
            else:
                message = "Query id provided is invalid!"

        return marshal(prepare_response(message, status, carve_session), parent_wrappers.common_response_wrapper )


@api.resource('/carves/delete', endpoint='delete carves by session id')
class DeleteCarveSessionByPostSessionId(Resource):
    """
        Delete Carves session by session id
    """
    parser = requestparse(['session_id'], [str], ["session id"], [True])

    @admin_required
    def post(self):
        args = self.parser.parse_args()
        session_ids = args['session_id'].split(',')
        all_carves = carves_dao.get_all_carves_by_session_ids(session_ids)
        session_ids = [session.session_id for session in all_carves]
        carve_ids = [session.id for session in all_carves]
        if session_ids:
            carves_dao.delete_carve_by_session_ids(session_ids)
            bulk_insert_to_pa(db.session, 'deleted', CarveSession, carve_ids)
            db.session.commit()
            current_app.logger.warning("Carve {} are deleted permanently".format(session_ids))
            message = "Successfully deleted the Carve for the session id given!"
            status = "success"
        else:
            message = "No Carve is found for the session id provided!"
            status = "failure"

        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
