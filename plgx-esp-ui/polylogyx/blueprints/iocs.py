import os
from werkzeug import datastructures

from flask_restplus import Namespace, Resource, marshal

from polylogyx.models import Alerts
from .utils import *
from polylogyx.utils import require_api_key
from polylogyx.dao import iocs_dao as dao
from polylogyx.wrappers import parent_wrappers as parentwrapper
from polylogyx.wrappers import ioc_wrappers

ns = Namespace('iocs', description='iocs related operations')


@require_api_key
@ns.route('/', endpoint='get_ioc_data')
@ns.doc(params={})
class ListIocs(Resource):
    """lists ioc json data"""
    def get(self):
        data = marshal(dao.get_intel_data('self'), ioc_wrappers.ioc_wrapper, skip_none=True)
        if data:
            status="success"
            message="Successfully fetched the ioc files"
        else:
            status = "failure"
            message = "There is no intel data to display.."
        return marshal(prepare_response(message,status,data),parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/add', endpoint='add_ioc')
@ns.doc(params={'file': 'ioc json file to upload'})
class AddIocs(Resource):
    """uploads and adds an ioc file to the iocs folder"""
    parser = requestparse(['file'], [datastructures.FileStorage], ['Threat file'], [True])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        file=args['file']
        content = file.read().decode("utf-8")
        try:
            intel = json.loads(content)
            data = intel['data']
            dao.del_manual_threat_intel(Alerts.SOURCE_IOC)

            for intel_name, values in data.items():
                for value in values['values']:
                    dao.create_manual_threat_intel(intel_type='self', type=values['type'],value=value,severity=values['severity'], threat_name=intel_name)
            message="Successfully updated the intel from the file uploaded"
            status='success'
        except Exception as e:
            message = str(e)
            #message='Invalid JSON format...! Please upload JSON file only'
            status='failure'
        return marshal(prepare_response(message,status),parentwrapper.common_response_wrapper,skip_none=True)
