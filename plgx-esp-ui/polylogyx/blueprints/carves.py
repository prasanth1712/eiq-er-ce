import json

from flask import request, send_file
from flask_restplus import Namespace, Resource, marshal

from .utils import *
from polylogyx.utils import require_api_key
from polylogyx.dao import carves_dao as dao
from polylogyx.dao import nodes_dao as nodedao
from polylogyx.wrappers import parent_wrappers as parentwrapper
from polylogyx.wrappers import carve_wrappers as wrapper
from polylogyx.models import DistributedQueryTask,db,CarveSession
ns = Namespace('carves', description='Carves related operations')


@require_api_key
@ns.route('/', endpoint='node_carves_list')
@ns.doc(params={'host_identifier': 'Host identifier of the Node'})
class NodeCarvesList(Resource):
    """lists out the carves for a specific node when host_identifier given otherwise returns all carves"""
    parser = requestparse(['host_identifier'],[str],["host identifier of the node"])

    @ns.expect(parser)
    def post(self):
        carves = None
        status = 'success'
        host_identifier = self.parser.parse_args()['host_identifier']

        if host_identifier:
            node = nodedao.get_node_by_host_identifier(host_identifier)
            if not node:
                status = 'failure'
                message = 'Node with this identifier does not exist'
            else:
                carves = dao.get_carves_by_node_id(node.id)
                carves = marshal(carves, wrapper.carves_wrapper)
                message = 'Successfully fetched the carves'
        else:
            carves = dao.get_carves_all()
            carves = marshal(carves, wrapper.carves_wrapper)
            message = 'Successfully fetched the carves'
        if not carves: message = "carves data doesn't exists for the input given"
        return marshal(prepare_response(message,status,carves),parentwrapper.common_response_wrapper)


@require_api_key
@ns.route('/download/<string:session_id>', endpoint='download_carves')
@ns.doc(params={'session_id': 'session id'})
class DownloadCarves(Resource):
    """download carves through session id"""

    def get(self, session_id):
        status = 'failure'
        message = 'Data missing'
        if not session_id:
            message = 'Please provide a session id'
        else:
            carve_session = dao.get_carves_by_session_id(session_id)
            if carve_session:
                data = send_file(current_app.config['BASE_URL'] + '/carves/' + carve_session.node.host_identifier + '/'+ carve_session.archive , as_attachment=True, mimetype='application/x-tar',attachment_filename='carve_session.tar')
                return data
            else:
                message = 'This session id does not exist'

        return marshal(prepare_response(message,status), parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/query/<int:query_id>/<string:host_identifier>', endpoint='get_carves_by_query_id')
@ns.doc(params={'query_id': 'query id','host_identifier': 'host identifier'})
class CarveSessionByQueryId(Resource):
    """download carves through session id"""

    def post(self, query_id, host_identifier):
        return self.func(query_id, host_identifier)

    def get(self, query_id, host_identifier):
        return self.func(query_id, host_identifier)

    def func(self, query_id, host_identifier):
        status = 'failure'
        message = 'Data missing'

        if not query_id:
            message = 'Please provide a query id'
        else:
            if host_identifier:
                node = nodedao.get_node_by_host_identifier(host_identifier)
                if not node:
                    status = 'failure'
                    message = 'Node with this identifier does not exist'
                else:

                    dqt=db.session.query(DistributedQueryTask).filter(DistributedQueryTask.distributed_query_id==query_id).filter(DistributedQueryTask.node_id==node.id).first()
                    if dqt:
                        carve_session=db.session.query(CarveSession).filter(CarveSession.request_id==dqt.guid).first()
                        carve_session = marshal(carve_session, wrapper.carves_wrapper)

                        if carve_session:
                            status = "success"
                            message="Successfully fetched the carve"
                            return marshal(prepare_response(message, status, carve_session), parentwrapper.common_response_wrapper)
                        else:
                            message="carve not started"
                    else:
                        message="query id provided is invalid"

        return marshal(prepare_response(message,status), parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/query', endpoint='get_carves_by_query_id_post')
@ns.doc(params={'query_id': 'query id','host_identifier': 'host identifier'})
class CarveSessionByPostQueryId(Resource):
    """downloads carves through session id"""
    parser = requestparse(['query_id', 'host_identifier'], [str, str], ["query id", "host_identifier"], [True, True])

    @ns.expect(parser)
    def post(self):
        status = 'failure'

        args = self.parser.parse_args()
        host_identifier = args['host_identifier']
        query_id = args['query_id']

        node = nodedao.get_node_by_host_identifier(host_identifier)
        if not node:
            message = 'Node with this identifier does not exist'
        else:
            dqt = db.session.query(DistributedQueryTask).filter(DistributedQueryTask.distributed_query_id == query_id).filter(DistributedQueryTask.node_id==node.id).first()
            if dqt:
                carve_session = db.session.query(CarveSession).filter(CarveSession.request_id == dqt.guid).first()
                carve_session = marshal(carve_session, wrapper.carves_wrapper)

                if carve_session:
                    status = "success"
                    message = "Successfully fetched the carve"
                    return marshal(prepare_response(message, status, carve_session), parentwrapper.common_response_wrapper)
                else:
                    message = "carve not started"
            else:
                message = "query id provided is invalid"

        return marshal(prepare_response(message, status), parentwrapper.common_response_wrapper, skip_none=True)
