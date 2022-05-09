import json
from sqlalchemy import cast

from flask_restplus import Namespace, Resource, marshal
from flask import request, jsonify


from .utils import *
from polylogyx.utils import require_api_key
from polylogyx.models import Alerts
from polylogyx.dao import alerts_dao as dao
from polylogyx.dao import nodes_dao as node_dao
from polylogyx.dao import rules_dao as rule_dao
from polylogyx.dao import distributed_dao as distributed_dao
from polylogyx.wrappers import alert_wrappers as alert_wrapper
from polylogyx.wrappers import node_wrappers as node_wrapper
from polylogyx.wrappers import parent_wrappers as parentwrapper


ns = Namespace('alerts', description='Alerts related operations')


@require_api_key
@ns.route('/', endpoint='alerts_post')
@ns.doc(params={'host_identifier': 'Host identifier of the Node', 'rule_id':'rule id', 'query_name':'query name'})
class ViewAlerts(Resource):
    """views the alerts"""
    parser = requestparse(['host_identifier', 'rule_id', 'query_name'], [str, int, str], ["host identifier of the node", "rule id", "query name"], [False, False, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()

        host_identifier = args['host_identifier']
        rule_id = args['rule_id']
        query_name = args['query_name']
        data_valid = True

        if host_identifier: node = node_dao.get_node_by_host_identifier(host_identifier)
        else: node = None

        alert_results = dao.get_alerts_for_input(node,rule_id,query_name)
        data = alert_results[0]
        message = alert_results[1]

        if not data: status="failure";
        else: data = add_rule_name_to_alerts_response(marshal(data, alert_wrapper.alerts_wrapper, skip_none=True)); message = "Successfully received the alerts"; status = "success";

        return marshal(prepare_response(message,status,data), parentwrapper.common_response_wrapper, skip_none=True)



@require_api_key
@ns.route('/data/<int:alert_id>', endpoint = "alerts_data")
@ns.doc(params = {'alert_id':"id of the alert"})
class AlertsData(Resource):
    """returns alert data"""

    def get(self,alert_id):
        data = {}
        if not alert_id:
            return marshal(prepare_response("Please! Provide the alert id", "failure"), parentwrapper.common_response_wrapper, skip_none=True)

        alert = dao.get_alert_by_id(alert_id)

        time = 0
        if alert:
            if 'time' in alert.message:
                time = alert.message['time']
            time = int(time)

            data['alert'] = marshal(alert, alert_wrapper.alerts_data_wrapper)
            data['node'] = alert.node.host_identifier
            message = "data is fetched successfully"
            status = "success"

        else:
            message = "there is no alert with this id"
            status = "failure"
            data = None
        if not data: message="alerts data doesn't exists for the input given"
        return marshal(prepare_response(message,status,data), parentwrapper.common_response_wrapper,skip_none=True)